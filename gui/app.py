"""Main application window: header, tabs, event pump, watcher wiring."""
from __future__ import annotations

import json
import math
import queue
from datetime import datetime, timezone
from pathlib import Path

import customtkinter as ctk

from core.database import Database
from core.router import Router
from core.settings_store import Settings
from core.watcher import Watcher
from gui import theme
from gui.customers_tab import CustomersTab
from gui.dialogs import NewCustomerDialog
from gui.errors_tab import ErrorsTab
from gui.logs_tab import LogsTab
from gui.settings_tab import SettingsTab
from gui.theme import C, FONT_TAGLINE, FONT_UI, FONT_WORDMARK, accent_button
from integrations.registry import label_for

APP_VERSION = "1.0.0"


class App(ctk.CTk):
    """Top-level window. Owns the DB, settings, watcher and all tabs."""

    def __init__(self, db: Database, settings: Settings, box, autostart: bool = False) -> None:
        super().__init__()
        self.db = db
        self.settings = settings
        self._box = box

        # Thread-safe channels from the watcher into the GUI.
        self._events: queue.Queue[dict] = queue.Queue()
        self._new_customers: queue.Queue[tuple[str, int]] = queue.Queue()

        self.title(f"InvoiceM8  v{APP_VERSION}")
        self.geometry("1080x720")
        self.minsize(920, 600)
        self.configure(fg_color=C["bg"])
        theme.dark_titlebar(self)

        self._running = False
        self._glow_job: str | None = None
        self._glow_phase = 0
        self._settings_win: ctk.CTkToplevel | None = None

        self._build_header()
        self._build_tabs()

        self.watcher = Watcher(
            db, settings,
            on_new_customer=lambda name, pid: self._new_customers.put((name, pid)),
            emit=self.emit_event,
            on_status=lambda running: self.after(0, self._set_status, running),
        )

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(400, self._pump)

        if autostart or settings.get_bool("watcher.autostart"):
            self.after(800, self.watcher.start)

    # -- header --------------------------------------------------
    def _build_header(self) -> None:
        bar = ctk.CTkFrame(self, fg_color=C["panel"], corner_radius=0, height=54)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        ctk.CTkLabel(bar, text="INVOICEM8", font=FONT_WORDMARK,
                     text_color=C["text"]).pack(side="left", padx=(16, 4))
        self._tagline = ctk.CTkLabel(bar, text="", font=FONT_TAGLINE, text_color=C["dim"])
        self._tagline.pack(side="left", padx=4)
        self._refresh_tagline()

        # Right-aligned controls (packed right-to-left): Scan now | Start/Stop | Settings
        accent_button(ctk, bar, "Settings", self._open_settings,
                      colour=C["btn_off"]).pack(side="right", padx=(4, 12))
        self._start_btn = accent_button(ctk, bar, "Start Watcher", self._toggle_watcher,
                                        colour=C["green"])
        self._start_btn.pack(side="right", padx=4)
        accent_button(ctk, bar, "Scan now", self._scan_now,
                      colour=C["blue"]).pack(side="right", padx=4)

    # -- tabs ---------------------------------------------------
    def _build_tabs(self) -> None:
        # Outer frame carries the "watcher running" glow border.
        self._glow = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=8,
                                  border_width=2, border_color=C["border"])
        self._glow.pack(fill="both", expand=True, padx=10, pady=10)

        self.tabs = ctk.CTkTabview(self._glow, fg_color=C["panel"])
        self.tabs.pack(fill="both", expand=True, padx=3, pady=3)
        for name in ("Customers", "Activity Log", "Error Log"):
            self.tabs.add(name)
        self.customers_tab = CustomersTab(self.tabs.tab("Customers"), self)
        self.logs_tab = LogsTab(self.tabs.tab("Activity Log"), self)
        self.errors_tab = ErrorsTab(self.tabs.tab("Error Log"), self)
        self.settings_tab: SettingsTab | None = None  # created on first open
        self.tabs.set("Activity Log")

    # -- settings window --------------------------------------
    def _open_settings(self) -> None:
        """Settings lives in its own window, opened from the header button."""
        if self._settings_win is not None and self._settings_win.winfo_exists():
            self._settings_win.lift()
            self._settings_win.focus()
            return
        win = ctk.CTkToplevel(self)
        win.title("InvoiceM8 - Settings")
        win.geometry("820x780")
        win.configure(fg_color=C["bg"])
        theme.dark_titlebar(win)
        self._settings_win = win
        self.settings_tab = SettingsTab(win, self)
        win.after(200, win.lift)

    # -- event pump (runs on the Tk main thread) ----------------
    def emit_event(self, **event) -> None:
        """Thread-safe: called by watcher/router to push a log line."""
        event.setdefault("ts", datetime.now(timezone.utc).isoformat(timespec="seconds"))
        # Persist non-error activity; errors are written by the router itself.
        if event.get("level") != "ERROR":
            self.db.add_activity(**{k: event.get(k, "") for k in
                                    ("ts", "level", "customer_name", "invoice_ref",
                                     "platform", "action", "filename", "message")})
        self._events.put(event)

    def _pump(self) -> None:
        """Drain queues and update the UI. Rescheduled every 400 ms."""
        try:
            while True:
                self.logs_tab.append_live(self._events.get_nowait())
        except queue.Empty:
            pass
        try:
            while True:
                name, pid = self._new_customers.get_nowait()
                self._handle_new_customer(name, pid)
        except queue.Empty:
            pass
        self.after(400, self._pump)

    # -- new customer modal + replay ---------------------------
    def _handle_new_customer(self, name: str, pending_id: int) -> None:
        """Show the modal; on accept, add the customer and route its queue."""
        dlg = NewCustomerDialog(
            self, name,
            label_for(self.settings.get("service.provider", "servicem8")),
            label_for(self.settings.get("accounting.provider", "none")),
        )
        self.wait_window(dlg)
        if not dlg.result:
            self.db.set_pending_status(pending_id, "skipped")
            self.emit_event(level="WARN", customer_name=name, action="skipped",
                            message="User skipped the new-customer prompt.")
            return

        self.customers_tab.add_from_dialog(dlg.result)
        self.emit_event(level="INFO", customer_name=dlg.result["name"], action="added",
                        message="Customer added via prompt; routing queued invoices.")
        self._replay_pending_for(dlg.result["name"], name)

    def _replay_pending_for(self, customer_name: str, extracted_name: str) -> None:
        """Route every pending invoice whose extracted name now resolves."""
        router = Router(self.db, self.settings, emit=self.emit_event)
        from core.parser_ai import ParseResult
        for row in self.db.list_pending("pending_new_customer"):
            if row["extracted_name"].strip().lower() not in (
                extracted_name.strip().lower(), customer_name.strip().lower()
            ):
                continue
            data = json.loads(row["raw_json"] or "{}")
            parsed = ParseResult(
                customer_name=customer_name,
                job_number=data.get("job_number", row["job_number"]),
                invoice_ref=data.get("invoice_ref", row["invoice_ref"]),
                amount_total=data.get("amount_total", ""),
                invoice_date=data.get("invoice_date", ""),
            )
            path = Path(row["file_path"])
            if path.exists():
                router.route(parsed, [path], row["email_subject"], row["email_from"])
            self.db.set_pending_status(row["id"], "resolved")
        self.refresh_logs()

    # -- misc callbacks ---------------------------------------
    def _toggle_watcher(self) -> None:
        if self.watcher.running:
            self.watcher.stop()
        else:
            self.watcher.start()

    def _scan_now(self) -> None:
        if not self.watcher.running:
            self.watcher.start()
        self.watcher.scan_now()

    def _set_status(self, running: bool) -> None:
        """Reflect watcher state in the toggle button and the glow border."""
        self._running = running
        self._start_btn.configure(
            text="Stop Watcher" if running else "Start Watcher",
            fg_color=C["red"] if running else C["green"],
            hover_color=theme.shade(C["red"] if running else C["green"], 0.82),
        )
        if running and self._glow_job is None:
            self._glow_phase = 0
            self._glow_tick()
        elif not running and self._glow_job is not None:
            self.after_cancel(self._glow_job)
            self._glow_job = None
            self._glow.configure(border_color=C["border"])

    def _glow_tick(self) -> None:
        """Pulse the tab-area border green while the watcher runs."""
        self._glow_phase = (self._glow_phase + 1) % 48
        t = (math.sin(self._glow_phase / 48 * 2 * math.pi) + 1) / 2  # 0..1
        self._glow.configure(border_color=theme.shade(C["green"], 0.55 + 0.95 * t))
        self._glow_job = self.after(80, self._glow_tick)

    def _refresh_tagline(self) -> None:
        """Header subtitle showing the selected Service and Accounting systems."""
        svc = label_for(self.settings.get("service.provider", "servicem8"))
        acct = label_for(self.settings.get("accounting.provider", "none"))
        self._tagline.configure(text=f"Outlook  >  {svc}  +  {acct}")

    def refresh_after_settings(self) -> None:
        """Called by the Settings tab after a save."""
        self._refresh_tagline()
        self.customers_tab.refresh()

    def refresh_logs(self) -> None:
        self.logs_tab.refresh()

    def _on_close(self) -> None:
        if self._glow_job is not None:
            self.after_cancel(self._glow_job)
            self._glow_job = None
        try:
            self.watcher.stop()
        finally:
            self.db.close()
            self.destroy()
