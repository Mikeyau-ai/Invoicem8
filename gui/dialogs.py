"""Modal dialogs - the 'new customer detected' prompt and the catch-up sweep."""
from __future__ import annotations

import customtkinter as ctk

from gui.theme import C, FONT_HEAD, FONT_UI, accent_button
from gui.theme import apply_icon


class NewCustomerDialog(ctk.CTkToplevel):
    """Asks whether to add an unrecognised customer and set routing toggles.

    Returns a dict via ``self.result`` (or ``None`` if dismissed):
        {name, aliases, servicem8_enabled, myob_enabled, accounting_enabled,
         file_types:[...]}
    """

    def __init__(self, master, extracted_name: str, service_label: str,
                 accounting_label: str) -> None:
        """Build the prompt, pre-filled with the extracted customer name."""
        super().__init__(master)
        apply_icon(self)
        self.title("New customer detected")
        self.configure(fg_color=C["bg"])
        # Sized to the content, capped to the screen, and resizable - the
        # accounting row is optional so the natural height varies.
        height = min(620, max(480, master.winfo_screenheight() - 160))
        self.geometry(f"560x{height}")
        self.minsize(480, 420)
        self.grab_set()
        self.result: dict | None = None

        # Buttons are packed FIRST against the bottom so they can never be
        # pushed off-screen by the form above them.
        btns = ctk.CTkFrame(self, fg_color=C["bg"])
        btns.pack(side="bottom", fill="x", padx=20, pady=(8, 16))

        ctk.CTkLabel(self, text="New customer detected", font=FONT_HEAD,
                     text_color=C["yellow"]).pack(anchor="w", padx=20, pady=(18, 2))
        ctk.CTkLabel(self, text=f'Invoice parsed as customer "{extracted_name}", which is '
                                f"not in the database.\nAdd them and configure routing?",
                     font=FONT_UI, text_color=C["dim"], justify="left").pack(anchor="w", padx=20)

        # Scrollable so a small screen can still reach every field.
        form = ctk.CTkScrollableFrame(self, fg_color=C["panel"])
        form.pack(fill="both", expand=True, padx=20, pady=16)

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
        # "Enable None / Disabled upload" is meaningless - only offer the
        # accounting toggle when an accounting system is actually configured.
        self._acct = ctk.CTkSwitch(
            form, text=f"Enable {accounting_label} upload (Accounting system)")
        if accounting_label and accounting_label.lower() not in ("none", "none / disabled"):
            self._acct.grid(row=5, column=0, sticky="w", padx=12, pady=4)

        ctk.CTkLabel(form, text="File types to process", font=FONT_UI,
                     text_color=C["text"]).grid(row=7, column=0, sticky="w", padx=12, pady=(8, 2))
        self._types = ctk.CTkEntry(form, width=380)
        self._types.insert(0, "pdf")
        self._types.grid(row=8, column=0, padx=12, pady=(0, 12))

        accent_button(ctk, btns, "Add & route", self._accept,
                      colour=C["green"]).pack(side="right", padx=(8, 0))
        accent_button(ctk, btns, "Skip this invoice", self._reject,
                      colour=C["btn_off"]).pack(side="right")

        self.protocol("WM_DELETE_WINDOW", self._reject)

    def _accept(self) -> None:
        """Validate the form and publish the result, then close."""
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
        """Dismiss without adding a customer."""
        self.result = None
        self.destroy()


class CatchUpDialog(ctk.CTkToplevel):
    """Configure a one-off catch-up sweep of old, unprocessed invoice mail.

    Publishes ``self.result`` as
    ``{"days_back": int, "job_floor": int, "job_ceiling": int}``, or ``None``
    if cancelled. The job bounds are deliberately NOT saved settings - they
    guard this single run so a backlog sweep only touches the jobs intended
    (e.g. skip jobs already closed, or file just one job / a small range).
    """

    def __init__(self, master) -> None:
        """Build the two-field prompt with its explanatory note."""
        super().__init__(master)
        apply_icon(self)
        self.title("Catch up on old mail")
        self.configure(fg_color=C["bg"])
        self.geometry("520x380")
        self.minsize(460, 340)
        self.grab_set()
        self.result: dict | None = None

        btns = ctk.CTkFrame(self, fg_color=C["bg"])
        btns.pack(side="bottom", fill="x", padx=20, pady=(8, 16))

        ctk.CTkLabel(self, text="Catch up on old mail", font=FONT_HEAD,
                     text_color=C["yellow"]).pack(anchor="w", padx=20, pady=(18, 2))
        ctk.CTkLabel(self, text="One-off scan of invoice emails already in the mailbox.\n"
                                "Use it after the app has been off, or on a new mailbox.",
                     font=FONT_UI, text_color=C["dim"], justify="left").pack(anchor="w", padx=20)

        form = ctk.CTkFrame(self, fg_color=C["panel"])
        form.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(form, text="Scan mail from the last (days)", font=FONT_UI,
                     text_color=C["text"]).grid(row=0, column=0, sticky="w", padx=12, pady=(14, 2))
        self._days = ctk.CTkEntry(form, width=90)
        self._days.insert(0, "90")
        self._days.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 12))

        ctk.CTkLabel(form, text="Only file jobs in this range (blank = file all)", font=FONT_UI,
                     text_color=C["text"]).grid(row=2, column=0, sticky="w", padx=12, pady=(0, 2))
        self._jobs = ctk.CTkEntry(form, width=170, placeholder_text="e.g. 15000  or  15000-15010")
        self._jobs.grid(row=3, column=0, sticky="w", padx=12, pady=(0, 12))

        ctk.CTkLabel(form, text="A bare number is a floor (skip anything below it); low-high is\n"
                                "a range. An invoice outside it - or one whose job number\n"
                                "can't be read - is skipped, not filed anywhere.",
                     font=FONT_UI, text_color=C["dim"], justify="left").grid(
                         row=4, column=0, sticky="w", padx=12, pady=(0, 10))

        accent_button(ctk, btns, "Run catch-up", self._accept,
                      colour=C["green"]).pack(side="right", padx=(8, 0))
        accent_button(ctk, btns, "Cancel", self._reject,
                      colour=C["btn_off"]).pack(side="right")
        self.protocol("WM_DELETE_WINDOW", self._reject)

    def _accept(self) -> None:
        """Validate the days field, parse the job range, then close.

        Accepts ``""`` (all jobs), ``N`` / ``N-`` (floor only), ``-M`` (ceiling
        only) or ``N-M`` (inclusive range, ends swapped if reversed).
        """
        try:
            days = int(self._days.get().strip() or "90")
        except ValueError:
            self._days.configure(border_color=C["red"])
            return

        raw = self._jobs.get().strip().replace(" ", "")
        floor = ceiling = 0
        if raw:
            lo, sep, hi = raw.partition("-")
            try:
                floor = int(lo) if lo else 0
                ceiling = int(hi) if hi else 0
                if not sep:                     # bare "N" -> floor only
                    ceiling = 0
            except ValueError:
                self._jobs.configure(border_color=C["red"])
                return
            if floor and ceiling and floor > ceiling:
                floor, ceiling = ceiling, floor

        self.result = {"days_back": max(1, days),
                       "job_floor": max(0, floor), "job_ceiling": max(0, ceiling)}
        self.destroy()

    def _reject(self) -> None:
        """Dismiss without running a sweep."""
        self.result = None
        self.destroy()
