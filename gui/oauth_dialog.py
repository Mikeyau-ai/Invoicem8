"""Small helper dialog to complete a provider's one-time OAuth consent.

Opens the provider auth page in the browser, then the user pastes the
``code`` from the redirect URL back here to be exchanged for a refresh token.
"""
from __future__ import annotations

import customtkinter as ctk

from gui.theme import C, FONT_HEAD, FONT_UI, accent_button
from integrations.registry import build_provider


class OAuthDialog(ctk.CTkToplevel):
    """Guided authorization-code exchange."""

    def __init__(self, master, provider_key: str, settings, status_label) -> None:
        super().__init__(master)
        self.title("Authorise provider")
        self.configure(fg_color=C["bg"])
        self.geometry("520x260")
        self.grab_set()
        self._settings = settings
        self._status = status_label
        self._provider = build_provider(provider_key, settings)

        ctk.CTkLabel(self, text=f"Authorise {self._provider.label}", font=FONT_HEAD,
                     text_color=C["purple"]).pack(anchor="w", padx=18, pady=(16, 4))
        ctk.CTkLabel(self, text="1. Click 'Open consent page' and sign in.\n"
                                "2. Copy the 'code' value from the redirected URL.\n"
                                "3. Paste it below and click 'Exchange'.",
                     font=FONT_UI, text_color=C["dim"], justify="left").pack(anchor="w", padx=18)

        accent_button(ctk, self, "Open consent page",
                      self._open, colour=C["blue"]).pack(anchor="w", padx=18, pady=10)

        self._code = ctk.CTkEntry(self, width=470, placeholder_text="Paste authorization code")
        self._code.pack(padx=18, pady=6)
        accent_button(ctk, self, "Exchange for token", self._exchange,
                      colour=C["green"]).pack(anchor="w", padx=18, pady=8)
        self._msg = ctk.CTkLabel(self, text="", font=FONT_UI, text_color=C["dim"])
        self._msg.pack(anchor="w", padx=18)

    def _open(self) -> None:
        try:
            url = self._provider.authorize_interactive()
            self._msg.configure(text="Browser opened. If not, copy the URL from logs.",
                                text_color=C["dim"])
        except Exception as exc:
            self._msg.configure(text=f"Failed: {exc}", text_color=C["red"])

    def _exchange(self) -> None:
        try:
            self._provider.exchange_code(self._code.get())
            self._msg.configure(text="Refresh token stored.", text_color=C["green"])
            self._status.configure(text=f"{self._provider.label} authorised.",
                                   text_color=C["green"])
        except Exception as exc:
            self._msg.configure(text=f"Exchange failed: {exc}", text_color=C["red"])
