"""Modal dialogs - currently the 'new customer detected' prompt."""
from __future__ import annotations

import customtkinter as ctk

from gui.theme import C, FONT_HEAD, FONT_UI, accent_button


class NewCustomerDialog(ctk.CTkToplevel):
    """Asks whether to add an unrecognised customer and set routing toggles.

    Returns a dict via ``self.result`` (or ``None`` if dismissed):
        {name, aliases, servicem8_enabled, myob_enabled, accounting_enabled,
         file_types:[...]}
    """

    def __init__(self, master, extracted_name: str, service_label: str,
                 accounting_label: str) -> None:
        super().__init__(master)
        self.title("New customer detected")
        self.configure(fg_color=C["bg"])
        self.geometry("460x430")
        self.resizable(False, False)
        self.grab_set()
        self.result: dict | None = None

        ctk.CTkLabel(self, text="New customer detected", font=FONT_HEAD,
                     text_color=C["yellow"]).pack(anchor="w", padx=20, pady=(18, 2))
        ctk.CTkLabel(self, text=f'Invoice parsed as customer "{extracted_name}", which is '
                                f"not in the database.\nAdd them and configure routing?",
                     font=FONT_UI, text_color=C["dim"], justify="left").pack(anchor="w", padx=20)

        form = ctk.CTkFrame(self, fg_color=C["panel"])
        form.pack(fill="x", padx=20, pady=16)

        ctk.CTkLabel(form, text="Customer name", font=FONT_UI,
                     text_color=C["text"]).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 2))
        self._name = ctk.CTkEntry(form, width=380)
        self._name.insert(0, extracted_name)
        self._name.grid(row=1, column=0, padx=12, pady=(0, 10))

        ctk.CTkLabel(form, text="Also match these names (comma separated)", font=FONT_UI,
                     text_color=C["text"]).grid(row=2, column=0, sticky="w", padx=12, pady=(0, 2))
        self._aliases = ctk.CTkEntry(form, width=380, placeholder_text="ACME Pty Ltd, ACME Group")
        self._aliases.grid(row=3, column=0, padx=12, pady=(0, 12))

        self._sm8 = ctk.CTkSwitch(form, text=f"Enable {service_label} upload (Service system)")
        self._sm8.grid(row=4, column=0, sticky="w", padx=12, pady=4)
        self._sm8.select()
        self._acct = ctk.CTkSwitch(form, text=f"Enable {accounting_label} upload (Accounting system)")
        self._acct.grid(row=5, column=0, sticky="w", padx=12, pady=4)

        ctk.CTkLabel(form, text="File types to process", font=FONT_UI,
                     text_color=C["text"]).grid(row=7, column=0, sticky="w", padx=12, pady=(8, 2))
        self._types = ctk.CTkEntry(form, width=380)
        self._types.insert(0, "pdf")
        self._types.grid(row=8, column=0, padx=12, pady=(0, 12))

        btns = ctk.CTkFrame(self, fg_color=C["bg"])
        btns.pack(fill="x", padx=20, pady=(0, 16))
        accent_button(ctk, btns, "Add & route", self._accept,
                      colour=C["green"]).pack(side="right", padx=(8, 0))
        accent_button(ctk, btns, "Skip this invoice", self._reject,
                      colour=C["btn_off"]).pack(side="right")

        self.protocol("WM_DELETE_WINDOW", self._reject)

    def _accept(self) -> None:
        name = self._name.get().strip()
        if not name:
            self._name.configure(border_color=C["red"])
            return
        self.result = {
            "name": name,
            "aliases": [a.strip() for a in self._aliases.get().split(",") if a.strip()],
            "servicem8_enabled": bool(self._sm8.get()),
            "myob_enabled": False,
            "accounting_enabled": bool(self._acct.get()),
            "file_types": [t.strip().lower() for t in self._types.get().split(",") if t.strip()] or ["pdf"],
        }
        self.destroy()

    def _reject(self) -> None:
        self.result = None
        self.destroy()
