"""Activity Log tab - searchable history of what moved where and when.

Rows are read from ``activity_log`` in SQLite. The watcher also streams live
lines here through the app's event queue.
"""
from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from gui.theme import C, FONT_DATA, FONT_HEAD, FONT_UI, accent_button


class LogsTab:
    """Scrolling, filterable activity view backed by the DB."""

    def __init__(self, parent, app) -> None:
        self._app = app
        self._db = app.db

        root = ctk.CTkFrame(parent, fg_color=C["bg"])
        root.pack(fill="both", expand=True)

        bar = ctk.CTkFrame(root, fg_color=C["bg"])
        bar.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(bar, text="Activity Log", font=FONT_HEAD,
                     text_color=C["blue"]).pack(side="left", padx=6)
        self._search = ctk.CTkEntry(bar, width=280, placeholder_text="Search customer / ref / platform / text")
        self._search.pack(side="left", padx=6)
        self._search.bind("<Return>", lambda _e: self.refresh())
        self._search.bind("<Escape>", lambda _e: self._clear_filter())
        accent_button(ctk, bar, "Search", self.refresh, colour=C["blue"]).pack(side="left")
        accent_button(ctk, bar, "Clear filter", self._clear_filter,
                      colour=C["btn_off"]).pack(side="left", padx=6)
        accent_button(ctk, bar, "Clear log", self._clear_log,
                      colour=C["btn_off"]).pack(side="left")

        self._box = ctk.CTkTextbox(root, font=FONT_DATA, wrap="none",
                                   fg_color=C["row"], text_color=C["text"])
        self._box.pack(fill="both", expand=True)
        self._box.configure(state="disabled")
        self._configure_tags()
        self.refresh()

    def _configure_tags(self) -> None:
        """Colour lines by level (matches RamBo's issue colouring)."""
        for name, colour in (("INFO", C["text"]), ("WARN", C["yellow"]),
                             ("ERROR", C["red"])):
            self._box.tag_config(name, foreground=colour)

    def _clear_filter(self) -> None:
        """Reset the search box and show all recent activity again."""
        self._search.delete(0, "end")
        self.refresh()

    def _clear_log(self) -> None:
        """Permanently delete the stored activity history (with confirmation)."""
        if not messagebox.askyesno(
            "Clear activity log",
            "Delete all activity log entries from the database?\n"
            "This cannot be undone. (The error log is not affected.)",
            icon="warning", parent=self._box.winfo_toplevel(),
        ):
            return
        removed = self._db.clear_activity_log()
        self._box.configure(state="normal")
        self._box.delete("1.0", "end")
        self._box.configure(state="disabled")
        self._app.emit_event(level="INFO", action="log",
                             message=f"Activity log cleared ({removed} entries removed).")

    def refresh(self, *_a) -> None:
        """Re-query the DB and repaint."""
        term = self._search.get().strip()
        rows = self._db.search_activity(term)
        self._box.configure(state="normal")
        self._box.delete("1.0", "end")
        for r in reversed(rows):  # oldest first
            line = (f"{r['ts']}  {r['level']:5}  {r['platform']:>12}  "
                    f"{(r['customer_name'] or '-'):20.20}  {(r['invoice_ref'] or '-'):12.12}  "
                    f"{r['action']:10}  {r['filename']:24.24}  {r['message']}\n")
            self._box.insert("end", line, r["level"])
        self._box.see("end")
        self._box.configure(state="disabled")

    def append_live(self, event: dict) -> None:
        """Append one streamed watcher event without a full DB re-read."""
        term = self._search.get().strip().lower()
        text = " ".join(str(v) for v in event.values()).lower()
        if term and term not in text:
            return
        level = event.get("level", "INFO")
        line = (f"{event.get('ts', '')}  {level:5}  {event.get('platform', '-'):>12}  "
                f"{(event.get('customer_name') or '-'):20.20}  "
                f"{(event.get('invoice_ref') or '-'):12.12}  "
                f"{event.get('action', ''):10}  {event.get('filename', ''):24.24}  "
                f"{event.get('message', '')}\n")
        self._box.configure(state="normal")
        self._box.insert("end", line, level)
        self._box.see("end")
        self._box.configure(state="disabled")
