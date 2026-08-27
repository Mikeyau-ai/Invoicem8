"""Background inbox watcher.

A single daemon thread that:
  * on start, does a back-check for everything since the last processed email
    (or unread mail) so overnight invoices are not missed;
  * then polls Outlook every ``watcher.poll_minutes`` minutes;
  * parses each new invoice email and hands it to the :class:`Router`.

All UI communication is through thread-safe callbacks (``emit`` for log lines,
``on_new_customer`` for the modal, ``on_status`` for the run indicator).
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone

from dateutil import parser as dtparse

from core.database import Database
from core.parser_ai import InvoiceParser
from core.router import Router
from integrations.email_outlook import build_backend

log = logging.getLogger(__name__)


class Watcher:
    """Owns the polling thread and its lifecycle."""

    def __init__(self, db: Database, settings, on_new_customer=None,
                 emit=None, on_status=None) -> None:
        self._db = db
        self._settings = settings
        self._emit = emit or (lambda **_: None)
        self._on_status = on_status or (lambda running: None)
        self._router = Router(db, settings, on_new_customer=on_new_customer, emit=self._emit)
        self._parser = InvoiceParser(settings)
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._wake = threading.Event()

    # -- lifecycle ---------------------------------------------------
    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.running:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="InvoiceM8-Watcher", daemon=True)
        self._thread.start()
        self._on_status(True)
        self._emit(level="INFO", action="watcher", message="Watcher started.")

    def stop(self) -> None:
        """Signal the thread and wait briefly for it to exit. Idempotent.

        The thread is a daemon, so if it is stuck in a network call it is left
        to finish on its own and the process can still exit cleanly - the DB
        guards against a late write from it.
        """
        already_stopping = self._stop.is_set()
        self._stop.set()
        self._wake.set()
        if self._thread and self._thread.is_alive() and not already_stopping:
            self._thread.join(timeout=5)
        self._on_status(False)
        self._emit(level="INFO", action="watcher", message="Watcher stopped.")

    def scan_now(self) -> None:
        """Force an immediate poll (used by the 'Scan now' button)."""
        self._wake.set()

    # -- main loop -------------------------------------------------
    def _run(self) -> None:
        try:
            self._back_check()
        except Exception as exc:
            log.exception("Back-check failed")
            self._emit(level="ERROR", action="back_check", message=str(exc))

        while not self._stop.is_set():
            interval = max(1, self._settings.get_int("watcher.poll_minutes", 5)) * 60
            self._wake.wait(timeout=interval)
            self._wake.clear()
            if self._stop.is_set():
                break
            try:
                self._poll(since=self._resume_point(), unread_only=self._settings.get_bool("watcher.unread_only"))
            except Exception as exc:
                log.exception("Poll failed")
                self._emit(level="ERROR", action="poll", message=str(exc))

    def _resume_point(self) -> datetime | None:
        """Timestamp to fetch mail from - the newest email we have handled."""
        last = self._db.last_seen_email_time()
        if not last:
            return None
        try:
            return dtparse.isoparse(last).astimezone(timezone.utc)
        except (ValueError, TypeError):
            return None

    def _back_check(self) -> None:
        """Startup sweep: unread + anything since we last ran."""
        self._emit(level="INFO", action="back_check",
                   message="Startup back-check for missed invoices...")
        self._poll(since=self._resume_point(), unread_only=False, back_check=True)

    def _poll(self, since, unread_only: bool, back_check: bool = False) -> None:
        """One inbox scan -> parse -> route cycle."""
        backend = build_backend(self._settings)
        allowed_ext = set()  # per-customer filtering happens in the router
        messages = backend.fetch(since=since, unread_only=unread_only, allowed_ext=allowed_ext)
        if not messages:
            if not back_check:
                self._emit(level="INFO", action="poll", message="No new invoice emails.")
            return

        for msg in sorted(messages, key=lambda m: m.received_at):
            if self._stop.is_set():
                return
            if self._db.is_email_processed(msg.message_id):
                continue
            self._emit(level="INFO", customer_name="", platform="-", action="found",
                       message=f"Processing '{msg.subject}' from {msg.sender}")
            try:
                parsed = self._parser.parse(msg.subject, msg.body, msg.attachments)
                self._emit(level="INFO", customer_name=parsed.customer_name,
                           invoice_ref=parsed.invoice_ref, platform="-", action="parsed",
                           message=f"job={parsed.job_number or '-'} "
                                   f"ref={parsed.invoice_ref or '-'} "
                                   f"conf={parsed.confidence:.2f} src={parsed.source}")
                result = self._router.route(parsed, msg.attachments, msg.subject, msg.sender)
            except Exception as exc:
                log.exception("Message processing failed")
                self._db.add_error(stage="parse", filename=msg.subject,
                                   error=str(exc))
                self._emit(level="ERROR", action="parse", message=str(exc))
                result = "error"

            self._db.mark_email_processed(
                msg.message_id,
                received_at=msg.received_at.isoformat(),
                subject=msg.subject,
                result=result,
            )
