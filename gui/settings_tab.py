"""Settings tab.

Layout:
  * Deployment - three dropdowns: Service system, Accounting system, AI Provider.
  * Credential sections are rendered DYNAMICALLY - only the fields for the
    currently-selected service system, accounting system, Outlook backend and
    AI provider are shown. Changing a dropdown re-renders in place.

Secrets are Fernet-encrypted by :class:`Settings`; hidden providers keep their
stored values (switching back reveals them again).
"""
from __future__ import annotations

import customtkinter as ctk

from core import startup as win_startup
from gui.help_content import FIELD_HELP, SETUP_GUIDES
from core.parser_ai import AI_PROVIDERS
from gui.help_dialog import GuideWindow, HelpPopup
from gui.theme import C, FONT_HEAD, FONT_UI, accent_button
from integrations.email_outlook import build_backend
from integrations.registry import (
    ACCOUNTING_PROVIDERS,
    SERVICE_PROVIDERS,
    build_provider,
)

# Outlook field groups keyed by backend.
OUTLOOK_COMMON = [
    ("outlook.account", "Mailbox / account to monitor", False),
    ("outlook.folder", "Folder name", False),
]
OUTLOOK_BY_BACKEND = {
    "com": [],  # COM uses the signed-in desktop Outlook - no credentials
    "graph": [
        ("outlook.graph_tenant_id", "Graph Tenant ID", True),
        ("outlook.graph_client_id", "Graph Client ID", True),
        ("outlook.graph_client_secret", "Graph Client Secret", True),
        ("outlook.graph_refresh_token", "Graph Refresh Token", True),
    ],
}


class SettingsTab:
    """Builds and manages the Settings tab widgets."""

    def __init__(self, parent, app) -> None:
        self._app = app
        self._settings = app.settings
        self._fields: dict[str, ctk.CTkEntry] = {}

        self.frame = ctk.CTkScrollableFrame(parent, fg_color=C["bg"])
        self.frame.pack(fill="both", expand=True)

        self._build_deployment()
        # Dynamic containers - repopulated by _render().
        self._svc_box = ctk.CTkFrame(self.frame, fg_color=C["bg"])
        self._svc_box.pack(fill="x")
        self._acct_box = ctk.CTkFrame(self.frame, fg_color=C["bg"])
        self._acct_box.pack(fill="x")
        self._outlook_box = ctk.CTkFrame(self.frame, fg_color=C["bg"])
        self._outlook_box.pack(fill="x")
        self._ai_box = ctk.CTkFrame(self.frame, fg_color=C["bg"])
        self._ai_box.pack(fill="x")

        self._build_watcher()
        self._build_updates()
        self._build_actions()

        self.load()

    # -- static: deployment selectors ---------------------------
    def _build_deployment(self) -> None:
        self._header(self.frame, "Deployment")
        self._service = self._dropdown(
            self.frame, "Service system",
            [c.label for c in SERVICE_PROVIDERS.values()], self._render)
        self._accounting = self._dropdown(
            self.frame, "Accounting system",
            [c.label for c in ACCOUNTING_PROVIDERS.values()], self._render)
        self._ai_provider = self._dropdown(
            self.frame, "AI Provider",
            [m["label"] for m in AI_PROVIDERS.values()], self._render)

    def _build_watcher(self) -> None:
        self._header(self.frame, "Watcher")
        wrap = ctk.CTkFrame(self.frame, fg_color=C["bg"])
        wrap.pack(fill="x", padx=6, pady=3)
        ctk.CTkLabel(wrap, text="Poll interval (minutes)", font=FONT_UI,
                     text_color=C["text"], width=250, anchor="w").pack(side="left")
        self._poll = ctk.CTkEntry(wrap, width=80)
        self._poll.pack(side="left")
        self._unread_only = ctk.CTkSwitch(
            self.frame,
            text="Only process UNREAD emails  (off = every invoice since the last check)")
        self._unread_only.pack(anchor="w", padx=6, pady=4)
        self._autostart = ctk.CTkSwitch(self.frame, text="Start watcher automatically on app launch")
        self._autostart.pack(anchor="w", padx=6, pady=4)
        self._run_startup = ctk.CTkSwitch(self.frame, text="Run InvoiceM8 on Windows startup")
        self._run_startup.pack(anchor="w", padx=6, pady=4)

    def _build_updates(self) -> None:
        from core import updater
        from version import APP_VERSION

        self._header(self.frame, "Updates")
        ctk.CTkLabel(self.frame, text=f"Current version: {APP_VERSION}"
                     + ("" if updater.is_frozen() else "  (running from source)"),
                     font=FONT_UI, text_color=C["dim"]).pack(anchor="w", padx=6)
        self._auto_update = ctk.CTkSwitch(
            self.frame, text="Automatically check for updates on launch",
            command=lambda: updater.set_enabled(bool(self._auto_update.get())))
        self._auto_update.pack(anchor="w", padx=6, pady=4)
        row = ctk.CTkFrame(self.frame, fg_color=C["bg"])
        row.pack(fill="x", padx=6, pady=2)
        accent_button(ctk, row, "Check for updates now",
                      lambda: self._app.check_updates_now(
                          lambda t: self._status.configure(text=t, text_color=C["dim"])),
                      colour=C["blue"]).pack(side="left")
        accent_button(ctk, row, "About / Changelog", self._app.open_about,
                      colour=C["btn_off"]).pack(side="left", padx=8)

    def _build_actions(self) -> None:
        bar = ctk.CTkFrame(self.frame, fg_color=C["bg"])
        bar.pack(fill="x", padx=6, pady=18)
        accent_button(ctk, bar, "Save settings", self._save, colour=C["green"]).pack(side="left")
        accent_button(ctk, bar, "Test service", self._test_service, colour=C["blue"]).pack(side="left", padx=8)
        accent_button(ctk, bar, "Test accounting", self._test_accounting, colour=C["blue"]).pack(side="left")
        accent_button(ctk, bar, "Test Outlook", self._test_outlook, colour=C["blue"]).pack(side="left", padx=8)
        accent_button(ctk, bar, "Authorise OAuth", self._oauth, colour=C["purple"]).pack(side="left", padx=(8, 0))
        accent_button(ctk, bar, "Setup guide (all)", self._open_full_guide, colour=C["btn_off"]).pack(side="left", padx=8)
        # Status can be a long multi-line diagnostic (Test Outlook reports what
        # it scanned), so wrap it and let it grow instead of clipping.
        self._status = ctk.CTkLabel(self.frame, text="", font=FONT_UI,
                                    text_color=C["dim"], anchor="w",
                                    justify="left", wraplength=700)
        self._status.pack(anchor="w", fill="x", padx=6, pady=(0, 12))
        self.frame.bind(
            "<Configure>",
            lambda e: self._status.configure(wraplength=max(360, e.width - 40)))

    # -- widget helpers ----------------------------------------
    def _header(self, parent, text: str, guide_key: str | None = None) -> None:
        """Section heading, optionally with a 'Setup guide' button on the right."""
        row = ctk.CTkFrame(parent, fg_color=C["bg"])
        row.pack(fill="x", padx=6, pady=(16, 4))
        ctk.CTkLabel(row, text=text, font=FONT_HEAD, text_color=C["blue"]
                     ).pack(side="left")
        if guide_key and guide_key in SETUP_GUIDES:
            ctk.CTkButton(
                row, text="Setup guide", width=100, height=24,
                fg_color=C["btn_off"], hover_color=C["select"], font=FONT_UI,
                command=lambda k=guide_key: GuideWindow(
                    self._app, [(k, SETUP_GUIDES[k])]),
            ).pack(side="right")

    def _help_button(self, parent, key: str, label: str) -> None:
        """The little '?' that pops a HelpPopup for one field."""
        text = FIELD_HELP.get(key)
        if not text:
            return
        ctk.CTkButton(
            parent, text="?", width=24, height=24, corner_radius=12,
            fg_color=C["btn_off"], hover_color=C["blue"], font=FONT_HEAD,
            command=lambda: HelpPopup(self._app, label, text),
        ).pack(side="left", padx=(6, 0))

    def _dropdown(self, parent, label: str, values: list[str], on_change) -> ctk.CTkOptionMenu:
        wrap = ctk.CTkFrame(parent, fg_color=C["bg"])
        wrap.pack(fill="x", padx=6, pady=3)
        ctk.CTkLabel(wrap, text=label, font=FONT_UI, text_color=C["text"],
                     width=250, anchor="w").pack(side="left")
        menu = ctk.CTkOptionMenu(wrap, values=values, command=lambda *_: on_change())
        menu.pack(side="left")
        return menu

    def _row(self, parent, key: str, label: str, secret: bool) -> None:
        wrap = ctk.CTkFrame(parent, fg_color=C["bg"])
        wrap.pack(fill="x", padx=6, pady=3)
        ctk.CTkLabel(wrap, text=label, font=FONT_UI, text_color=C["text"],
                     width=250, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(wrap, show="•" if secret else "", width=400)
        entry.insert(0, self._settings.get(key, ""))
        entry.pack(side="left", fill="x", expand=True)
        self._help_button(wrap, key, label)
        self._fields[key] = entry

    def _note(self, parent, text: str) -> None:
        ctk.CTkLabel(parent, text=text, font=FONT_UI, text_color=C["dim"],
                     anchor="w", justify="left", wraplength=640).pack(anchor="w", padx=6, pady=(0, 4))

    # -- dynamic render --------------------------------------
    def _provider_key(self, menu: ctk.CTkOptionMenu, table) -> str:
        """Resolve the selected label back to a provider key."""
        label = menu.get()
        for k, cls in table.items():
            if cls.label == label:
                return k
        return next(iter(table))

    def _ai_key(self) -> str:
        """Resolve the AI Provider dropdown label back to its provider key."""
        label = self._ai_provider.get()
        for k, m in AI_PROVIDERS.items():
            if m["label"] == label:
                return k
        return "gemini"

    def _on_backend_change(self) -> None:
        """Remember the Outlook backend choice, then re-render."""
        self._ob_value = self._outlook_backend.get()
        self._render()

    def _render(self, *_a) -> None:
        """Rebuild every dynamic credential section from the current dropdowns."""
        # Every credential entry is recreated from settings on each render.
        self._fields = {}
        for box in (self._svc_box, self._acct_box, self._outlook_box, self._ai_box):
            for w in box.winfo_children():
                w.destroy()

        # --- service system ---
        svc_key = self._provider_key(self._service, SERVICE_PROVIDERS)
        svc_cls = SERVICE_PROVIDERS[svc_key]
        self._header(self._svc_box, f"Service system - {svc_cls.label}", guide_key=svc_key)
        if not svc_cls.setting_fields:
            self._note(self._svc_box, "No credentials required for this option.")
        for key, lbl, secret in svc_cls.setting_fields:
            self._row(self._svc_box, key, lbl, secret)
        if not svc_cls.implemented and svc_cls.setting_fields:
            self._note(self._svc_box, "Preview integration - fields are saved, "
                                      "but uploads are not wired yet.")

        # --- accounting system ---
        acct_key = self._provider_key(self._accounting, ACCOUNTING_PROVIDERS)
        acct_cls = ACCOUNTING_PROVIDERS[acct_key]
        self._header(self._acct_box, f"Accounting system - {acct_cls.label}", guide_key=acct_key)
        if not acct_cls.setting_fields:
            self._note(self._acct_box, "No credentials required for this option.")
        for key, lbl, secret in acct_cls.setting_fields:
            self._row(self._acct_box, key, lbl, secret)
        if not acct_cls.implemented and acct_cls.setting_fields:
            self._note(self._acct_box, "Preview integration - fields are saved, "
                                       "but uploads are not wired yet.")

        # --- Outlook ---
        backend = getattr(self, "_ob_value", None) or self._settings.get("outlook.backend", "com")
        self._header(self._outlook_box, "Outlook",
                     guide_key="outlook_graph" if backend == "graph" else "outlook_com")
        self._outlook_backend = self._dropdown(
            self._outlook_box, "Backend", ["com", "graph"], self._on_backend_change)
        self._outlook_backend.set(backend)
        self._ob_value = backend
        for key, lbl, secret in OUTLOOK_COMMON:
            self._row(self._outlook_box, key, lbl, secret)
        backend = self._outlook_backend.get()
        if backend == "com":
            self._note(self._outlook_box,
                       "COM backend reads the Outlook desktop client you are already "
                       "signed into - no extra credentials needed.")
        for key, lbl, secret in OUTLOOK_BY_BACKEND.get(backend, []):
            self._row(self._outlook_box, key, lbl, secret)

        # --- AI ---
        akey = self._ai_key()
        meta = AI_PROVIDERS[akey]
        self._header(self._ai_box, f"AI Provider - {meta['label']}", guide_key=akey)
        self._row(self._ai_box, "ai.model",
                  f"Model name (blank = {meta['default_model'] or 'server default'})", False)
        if meta["needs_base_url"]:
            self._row(self._ai_box, "ai.compat_base_url", "API base URL (ends in /v1)", False)
        klabel = "API Key" if meta["needs_key"] else "API Key (optional for local servers)"
        self._row(self._ai_box, meta["key_setting"], klabel, True)

    # -- load / save ----------------------------------------
    def load(self) -> None:
        """Populate the static selectors + watcher options from settings."""
        svc = self._settings.get("service.provider", "servicem8")
        self._service.set(SERVICE_PROVIDERS.get(svc, SERVICE_PROVIDERS["servicem8"]).label)
        acct = self._settings.get("accounting.provider", "none")
        self._accounting.set(ACCOUNTING_PROVIDERS.get(acct, ACCOUNTING_PROVIDERS["none"]).label)
        ai_prov = self._settings.get("ai.provider", "gemini")
        self._ai_provider.set(AI_PROVIDERS.get(ai_prov, AI_PROVIDERS["gemini"])["label"])
        self._poll.delete(0, "end")
        self._poll.insert(0, self._settings.get("watcher.poll_minutes", "5"))
        (self._unread_only.select if self._settings.get_bool("watcher.unread_only") else self._unread_only.deselect)()
        (self._autostart.select if self._settings.get_bool("watcher.autostart") else self._autostart.deselect)()
        (self._run_startup.select if win_startup.is_enabled() else self._run_startup.deselect)()
        from core import updater
        (self._auto_update.select if updater.auto_check_pref() else self._auto_update.deselect)()
        self._render()

    def _save(self) -> None:
        for key, entry in self._fields.items():
            self._settings.set(key, entry.get())
        self._settings.set("service.provider",
                           self._provider_key(self._service, SERVICE_PROVIDERS))
        self._settings.set("accounting.provider",
                           self._provider_key(self._accounting, ACCOUNTING_PROVIDERS))
        self._settings.set("ai.provider", self._ai_key())
        self._settings.set("outlook.backend", self._outlook_backend.get())
        self._settings.set("watcher.poll_minutes", self._poll.get() or "5")
        self._settings.set("watcher.unread_only", "1" if self._unread_only.get() else "0")
        self._settings.set("watcher.autostart", "1" if self._autostart.get() else "0")
        try:
            win_startup.set_enabled(bool(self._run_startup.get()))
        except Exception as exc:
            self._status.configure(text=f"Startup toggle failed: {exc}", text_color=C["red"])
            return
        self._app.refresh_after_settings()
        self._status.configure(text="Settings saved.", text_color=C["green"])

    # -- tests / oauth --------------------------------------
    def _test_service(self) -> None:
        self._save()
        res = build_provider(self._settings.get("service.provider"), self._settings).test_connection()
        self._status.configure(text=res.detail, text_color=C["green"] if res.ok else C["red"])

    def _test_accounting(self) -> None:
        self._save()
        res = build_provider(self._settings.get("accounting.provider"), self._settings).test_connection()
        self._status.configure(text=res.detail, text_color=C["green"] if res.ok else C["red"])

    def _test_outlook(self) -> None:
        self._save()
        try:
            backend = build_backend(self._settings)
            msgs = backend.fetch(since=None, unread_only=self._unread_only.get() == 1,
                                 allowed_ext=set())
            detail = getattr(backend, "last_scan", "") or f"{len(msgs)} message(s) found."
            self._status.configure(
                text=f"Outlook OK - {detail}",
                text_color=C["green"] if msgs else C["yellow"])
        except Exception as exc:
            self._status.configure(text=f"Outlook error: {exc}", text_color=C["red"])

    def _open_full_guide(self) -> None:
        """Setup guide covering every currently-selected section."""
        keys = [
            self._provider_key(self._service, SERVICE_PROVIDERS),
            self._provider_key(self._accounting, ACCOUNTING_PROVIDERS),
            "outlook_graph" if getattr(self, "_ob_value", "com") == "graph" else "outlook_com",
            self._ai_key(),
        ]
        sections = [(k, SETUP_GUIDES[k]) for k in keys if k in SETUP_GUIDES]
        GuideWindow(self._app, sections)

    def _oauth(self) -> None:
        self._save()
        from gui.oauth_dialog import OAuthDialog
        for key in (self._settings.get("service.provider"),
                    self._settings.get("accounting.provider")):
            prov = build_provider(key, self._settings)
            if prov.uses_oauth:
                OAuthDialog(self._app, key, self._settings, self._status)
                return
        self._status.configure(text="Neither selected provider uses OAuth.", text_color=C["dim"])
