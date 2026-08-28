"""Decides where a parsed invoice goes and performs the uploads.

Rules (from the spec):
  * Match extracted customer name against the local DB (name + aliases).
  * Unknown customer -> queue as ``pending_invoices`` and raise a UI prompt
    via the ``on_new_customer`` callback; routing for that invoice pauses.
  * Known customer -> for each enabled toggle, call the matching provider:
      - servicem8_enabled  -> the selected Service system
      - accounting_enabled -> the selected Accounting system
  * Duplicate guard: a document (by file hash, or customer+ref+type) is never
    uploaded to the same platform twice - see processed_documents.
  * Credit notes (doc_type == "credit") are routed as credits/vendor-credits
    where the provider supports it.
Every attempt is written to activity_log or error_log.
"""
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

from core.database import Database
from core.parser_ai import ParseResult
from integrations.provider_base import UploadContext
from integrations.registry import build_accounting_provider, build_service_provider

log = logging.getLogger(__name__)


class Router:
    """Routes one parsed invoice to the enabled destinations."""

    def __init__(self, db: Database, settings, on_new_customer=None, emit=None) -> None:
        """Wire the router to the DB, settings and the UI callbacks."""
        self._db = db
        self._settings = settings
        self._on_new_customer = on_new_customer          # callable(name, pending_id)
        self._emit = emit or (lambda **_: None)          # GUI log pump

    def _ctx(self, customer, parsed: ParseResult, file_path: Path,
             subject: str) -> UploadContext:
        """Assemble the provider-agnostic upload context."""
        return UploadContext(
            customer_name=customer["name"] if customer else parsed.customer_name,
            customer_external_id=(customer["accounting_contact_id"] if customer else ""),
            job_number=parsed.job_number,
            invoice_ref=parsed.invoice_ref,
            amount_total=parsed.amount_total,
            invoice_date=parsed.invoice_date,
            file_path=file_path,
            email_subject=subject,
            doc_type=parsed.doc_type,
        )

    @staticmethod
    def _file_hash(path: Path) -> str:
        """SHA-256 of the attachment bytes - identifies an identical file.

        Read in chunks so a large scanned PDF is never held in memory whole.
        """
        digest = hashlib.sha256()
        try:
            with path.open("rb") as fh:
                while chunk := fh.read(1 << 20):
                    digest.update(chunk)
        except OSError:
            return ""
        return digest.hexdigest()

    def route(self, parsed: ParseResult, attachments: list[Path],
              subject: str, sender: str) -> str:
        """Process every attachment for one email. Returns a short result tag."""
        customer = self._db.find_customer_by_name(parsed.customer_name)

        if customer is None:
            for path in attachments:
                pid = self._db.add_pending(
                    extracted_name=parsed.customer_name,
                    job_number=parsed.job_number,
                    invoice_ref=parsed.invoice_ref,
                    email_subject=subject,
                    email_from=sender,
                    file_path=str(path),
                    raw_json=json.dumps(parsed.as_dict()),
                )
                self._emit(level="WARN", customer_name=parsed.customer_name,
                           invoice_ref=parsed.invoice_ref, platform="-",
                           action="queued",
                           message=f"Unknown customer '{parsed.customer_name}' - awaiting review.")
                if self._on_new_customer:
                    self._on_new_customer(parsed.customer_name, pid)
            return "pending_new_customer"

        # Providers depend only on settings and the customer's toggles, not on
        # the file, so build them once per email rather than per attachment -
        # each construction otherwise costs a fresh OAuth token refresh.
        targets = self._targets_for(customer)
        if not targets:
            self._emit(level="WARN", customer_name=customer["name"],
                       invoice_ref=parsed.invoice_ref, platform="-", action="no_route",
                       message="Customer matched but no upload toggles enabled.")
            return "no_route"

        allowed = set(customer["file_types"].split(","))
        routed_any = False
        for path in attachments:
            ext = path.suffix.lower().lstrip(".")
            if allowed and ext not in allowed:
                self._emit(level="INFO", customer_name=customer["name"],
                           invoice_ref=parsed.invoice_ref, platform="-",
                           action="skipped", filename=path.name,
                           message=f"File type .{ext} not enabled for this customer.")
                continue
            ctx = self._ctx(customer, parsed, path, subject)
            routed_any |= self._dispatch(customer, ctx, targets)
        return "routed" if routed_any else "no_route"

    def _targets_for(self, customer) -> list:
        """Resolve the providers this customer's toggles point at.

        ``servicem8_enabled`` is the generic "Service system" toggle and
        ``accounting_enabled`` the "Accounting system" toggle - each resolves
        to whichever provider is selected in Settings.
        """
        targets = []
        if customer["servicem8_enabled"]:
            prov = build_service_provider(self._settings)
            if prov.key != "none":
                targets.append(prov)
        if customer["accounting_enabled"]:
            prov = build_accounting_provider(self._settings)
            if prov.key != "none" and prov.key not in {t.key for t in targets}:
                targets.append(prov)
        return targets

    def _dispatch(self, customer, ctx: UploadContext, targets=None) -> bool:
        """Fire each enabled provider for a single file.

        ``targets`` is the pre-resolved provider list from :meth:`_targets_for`;
        it is only rebuilt here when a caller (the error-tab retry) has none.
        """
        if targets is None:
            targets = self._targets_for(customer)
        if not targets:
            self._emit(level="WARN", customer_name=customer["name"],
                       invoice_ref=ctx.invoice_ref, platform="-", action="no_route",
                       filename=ctx.file_path.name,
                       message="Customer matched but no upload toggles enabled.")
            return False

        file_hash = self._file_hash(ctx.file_path)
        kind = "credit note" if ctx.is_credit else "invoice"

        ok_any = False
        for provider in targets:
            if not ctx.job_number and provider.category == "service":
                self._record_error("routing", ctx, provider.label,
                                   f"Missing job number for {provider.label} upload.")
                continue
            if not provider.configured():
                self._record_error("config", ctx, provider.label,
                                   f"{provider.label} credentials are incomplete.")
                continue

            # Duplicate guard: same file bytes, or same customer+ref+type,
            # already uploaded to this platform.
            dup = self._db.document_already_sent(
                file_hash, ctx.customer_name, ctx.invoice_ref, ctx.doc_type, provider.label)
            if dup:
                self._emit(level="WARN", customer_name=ctx.customer_name,
                           invoice_ref=ctx.invoice_ref, platform=provider.label,
                           action="duplicate", filename=ctx.file_path.name,
                           message=f"Skipped - this {kind} was already sent to "
                                   f"{provider.label} on {dup['ts']}.")
                continue

            try:
                result = provider.upload_invoice(ctx)
            except Exception as exc:  # never let one provider kill the run
                log.exception("Provider %s crashed", provider.label)
                self._record_error("upload", ctx, provider.label, str(exc))
                continue

            if result.ok:
                ok_any = True
                self._db.record_document_sent(
                    file_hash=file_hash, customer_name=ctx.customer_name,
                    invoice_ref=ctx.invoice_ref, doc_type=ctx.doc_type,
                    platform=result.platform, remote_id=result.remote_id,
                    filename=ctx.file_path.name)
                msg = f"[{kind}] {result.detail}"
                # Only emit: the GUI's emit_event() persists every non-error
                # event, so writing the row here as well logged each upload
                # twice. Every other event in this class emits only.
                self._emit(level="INFO", customer_name=ctx.customer_name,
                           invoice_ref=ctx.invoice_ref, platform=result.platform,
                           action="uploaded", filename=ctx.file_path.name, message=msg)
            else:
                self._record_error("upload", ctx, result.platform, result.detail)
        return ok_any

    def _record_error(self, stage: str, ctx: UploadContext, platform: str,
                      message: str) -> None:
        """Write an error row and mirror it to the live log pump."""
        payload = json.dumps({
            "customer_name": ctx.customer_name,
            "job_number": ctx.job_number,
            "invoice_ref": ctx.invoice_ref,
            "amount_total": ctx.amount_total,
            "invoice_date": ctx.invoice_date,
            "file_path": str(ctx.file_path),
            "email_subject": ctx.email_subject,
            "platform": platform,
        })
        self._db.add_error(stage=stage, customer_name=ctx.customer_name,
                           invoice_ref=ctx.invoice_ref, filename=ctx.file_path.name,
                           error=f"[{platform}] {message}", payload=payload)
        self._emit(level="ERROR", customer_name=ctx.customer_name,
                   invoice_ref=ctx.invoice_ref, platform=platform, action="error",
                   filename=ctx.file_path.name, message=message)

    # -- retry from the Error tab -----------------------------------
    def retry_from_payload(self, payload_json: str) -> bool:
        """Re-run a single failed upload from its stored JSON snapshot."""
        data = json.loads(payload_json)
        parsed = ParseResult(
            customer_name=data.get("customer_name", ""),
            job_number=data.get("job_number", ""),
            invoice_ref=data.get("invoice_ref", ""),
            amount_total=data.get("amount_total", ""),
            invoice_date=data.get("invoice_date", ""),
        )
        path = Path(data["file_path"])
        if not path.exists():
            self._emit(level="ERROR", customer_name=parsed.customer_name,
                       platform=data.get("platform", "-"), action="retry",
                       message=f"Cached file missing: {path}")
            return False
        customer = self._db.find_customer_by_name(parsed.customer_name)
        if customer is None:
            self._emit(level="ERROR", customer_name=parsed.customer_name,
                       platform="-", action="retry",
                       message="Customer still not in database.")
            return False
        return self._dispatch(customer, self._ctx(customer, parsed, path,
                                                  data.get("email_subject", "")))
