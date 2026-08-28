"""Dedicated Microsoft sign-in window for the Graph backend.

The device-code flow is easy to lose track of: the browser ends up on
Microsoft's "This is not the right page" redirect target, which looks like a
failure even when sign-in succeeded. This window is the single source of
truth - it shows the code, lets you copy it, and reports the real outcome
(which comes from the token, not the browser).
"""
from __future__ import annotations

import threading
import webbrowser

import customtkinter as ctk

from gui.theme import C, FONT_HEAD, FONT_UI, FONT_WORDMARK, accent_button

DEVICE_LOGIN_URL = "https://microsoft.com/devicelogin"


class GraphSignInDialog(ctk.CTkToplevel):
    """Shows the device code and waits for the sign-in to complete."""

    def __init__(self, master, settings, on_done=None) -> None:
        super().__init__(master)
        self._settings = settings
        self._on_done = on_done
        self._closed = False

        self.title("Sign in to Microsoft")
        self.geometry("560x420")
        self.configure(fg_color=C["bg"])
        self.attributes("-topmost", True)
        self.after(400, lambda: self.attributes("-topmost", False))
        self.protocol("WM_DELETE_WINDOW", self._close)

        ctk.CTkLabel(self, text="Microsoft sign-in", font=FONT_HEAD,
                     text_color=C["blue"]).pack(anchor="w", padx=20, pady=(16, 2))

        self._code_lbl = ctk.CTkLabel(self, text="...", font=FONT_WORDMARK,
                                      text_color=C["green"])
        self._code_lbl.pack(anchor="w", padx=20, pady=(4, 0))

        self._steps = ctk.CTkLabel(
            self, text="Starting sign-in...", font=FONT_UI, text_color=C["text"],
            anchor="w", justify="left", wraplength=500)
        self._steps.pack(anchor="w", padx=20, pady=(6, 6))

        btns = ctk.CTkFrame(self, fg_color=C["bg"])
        btns.pack(anchor="w", padx=20, pady=4)
        accent_button(ctk, btns, "Copy code", self._copy,
                      colour=C["btn_off"]).pack(side="left")
        accent_button(ctk, btns, "Open sign-in page", self._open,
                      colour=C["blue"]).pack(side="left", padx=8)

        ctk.CTkLabel(self, text="Status", font=FONT_UI,
                     text_color=C["blue"]).pack(anchor="w", padx=20, pady=(10, 2))
        # Selectable so the exact text can be copied when reporting a problem.
        self._status = ctk.CTkTextbox(self, height=120, wrap="word", font=FONT_UI,
                                      fg_color=C["row"], text_color=C["text"])
        self._status.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        self._close_btn = accent_button(ctk, self, "Close", self._close,
                                        colour=C["btn_off"])
        self._close_btn.pack(pady=(0, 12))

        self._code = ""
        self.after(100, self._start)

    # -- helpers -------------------------------------------------
    def _say(self, text: str, colour: str | None = None) -> None:
        """Replace the status text (safe to call from the Tk thread only)."""
        self._status.configure(state="normal")
        self._status.delete("1.0", "end")
        self._status.insert("1.0", text)
        if colour:
            self._status.configure(text_color=colour)
        self._status.configure(state="disabled")

    def _copy(self) -> None:
        if not self._code:
            return
        try:
            self.clipboard_clear()
            self.clipboard_append(self._code)
            self._say(f"Code {self._code} copied to the clipboard.", C["dim"])
        except Exception:
            pass

    def _open(self) -> None:
        try:
            webbrowser.open(DEVICE_LOGIN_URL)
        except Exception:
            self._say(f"Could not open a browser. Go to {DEVICE_LOGIN_URL} "
                      f"manually and enter {self._code}.", C["yellow"])

    def _close(self) -> None:
        self._closed = True
        self.destroy()

    # -- flow ---------------------------------------------------
    def _start(self) -> None:
        """Request a device code, then poll for completion off-thread."""
        from integrations.graph_auth import begin_device_login, complete_device_login

        try:
            flow, app, cache = begin_device_login(self._settings)
        except Exception as exc:
            self._code_lbl.configure(text="-", text_color=C["red"])
            self._steps.configure(text="Sign-in could not start.")
            self._say(str(exc), C["red"])
            return

        self._code = flow.get("user_code", "")
        self._code_lbl.configure(text=self._code)
        self._steps.configure(
            text=(f"1. A browser is opening {DEVICE_LOGIN_URL}\n"
                  f"2. Enter the code above and sign in as the mailbox account.\n"
                  f"3. Approve the permission request.\n\n"
                  f"The browser may finish on a Microsoft page saying 'This is "
                  f"not the right page' - that is normal and does NOT mean it "
                  f"failed. This window shows the real result."))
        # Copy/open first: both write to the status box, and the waiting
        # message must be the one left on screen.
        self._copy()
        self._open()
        self._say("Waiting for you to complete sign-in in the browser...",
                  C["yellow"])

        def work() -> None:
            try:
                who = complete_device_login(self._settings, flow, app, cache)
                msg, colour = (f"SUCCESS - signed in as {who}.\n\n"
                               f"You can close this window and click "
                               f"'Test mailbox'."), C["green"]
            except Exception as exc:
                msg, colour = f"FAILED\n\n{exc}", C["red"]
            if not self._closed:
                try:
                    self.after(0, lambda: self._finish(msg, colour))
                except Exception:
                    pass

        threading.Thread(target=work, daemon=True, name="graph-signin").start()

    def _finish(self, msg: str, colour: str) -> None:
        if self._closed:
            return
        self._say(msg, colour)
        self._steps.configure(text="Sign-in finished - see Status below.")
        if self._on_done:
            try:
                self._on_done()
            except Exception:
                pass
