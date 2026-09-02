"""Dedicated Microsoft sign-in window for the Graph backend.

The device-code flow is easy to lose track of: the browser ends up on
Microsoft's "This is not the right page" redirect target, which looks like a
failure even when sign-in succeeded. This window is the single source of
truth - it shows the code, lets you copy it, and reports the real outcome
(which comes from the token, not the browser).
"""
from __future__ import annotations

import logging
import threading
import webbrowser

import customtkinter as ctk

from gui.theme import C, FONT_HEAD, FONT_UI, FONT_WORDMARK, accent_button
from gui.theme import apply_icon

log = logging.getLogger(__name__)

DEVICE_LOGIN_URL = "https://microsoft.com/devicelogin"


class GraphSignInDialog(ctk.CTkToplevel):
    """Shows the device code and waits for the sign-in to complete."""

    def __init__(self, master, settings, on_done=None) -> None:
        """Build the window and immediately request a device code."""
        super().__init__(master)
        apply_icon(self)
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
        accent_button(ctk, btns, "Copy status text", self._copy_status,
                      colour=C["btn_off"]).pack(side="left")

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
        self._result = None
        self._verify_uri = ""
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
        """Put the device code on the clipboard."""
        if not self._code:
            return
        try:
            self.clipboard_clear()
            self.clipboard_append(self._code)
            self._say(f"Code {self._code} copied to the clipboard.", C["dim"])
        except Exception:
            pass

    def _copy_status(self) -> None:
        """Put the whole status message on the clipboard - no screenshot needed."""
        try:
            text = self._status.get("1.0", "end").strip()
            self.clipboard_clear()
            self.clipboard_append(text)
        except Exception:
            pass

    def _open(self) -> None:
        """Open the page the code was actually issued for.

        A device code is only redeemable at the verification URI belonging to
        the authority that minted it - a code issued against /consumers is
        rejected by the generic microsoft.com/devicelogin page ("that code
        didn't work"), so never hardcode the destination.
        """
        url = self._verify_uri or DEVICE_LOGIN_URL
        try:
            webbrowser.open(url)
        except Exception:
            self._say(f"Could not open a browser. Go to {url} manually and "
                      f"enter {self._code}.", C["yellow"])

    def _close(self) -> None:
        """Mark the dialog closed so the poller stops, then destroy it."""
        self._closed = True
        self.destroy()

    # -- flow ---------------------------------------------------
    def _start(self) -> None:
        """Request a device code, then poll for completion off-thread."""
        from integrations.graph_auth import begin_device_login, complete_device_login

        from integrations.graph_auth import config_report

        report = config_report(self._settings)
        log.info("Graph sign-in config:\n%s", report)
        if "EMPTY" in report or "SUSPICIOUS" in report:
            # Sending Microsoft a blank/malformed client_id produces wildly
            # misleading errors (including a login page that puts the password
            # in the URL), so stop here with a clear message instead.
            self._code_lbl.configure(text="-", text_color=C["red"])
            self._steps.configure(text="Sign-in not started - the Client ID is "
                                       "missing or malformed.")
            self._say("CANNOT SIGN IN - fix the Client ID first.\n\n" + report,
                      C["red"])
            return

        try:
            flow, app, cache = begin_device_login(self._settings)
        except Exception as exc:
            self._code_lbl.configure(text="-", text_color=C["red"])
            self._steps.configure(text="Sign-in could not start.")
            log.error("Graph sign-in could not start: %s", exc)
            self._say(str(exc), C["red"])
            return

        self._code = flow.get("user_code", "")
        # verification_uri_complete embeds the code (one click, no typing);
        # verification_uri is the plain page for this authority.
        self._verify_uri = (flow.get("verification_uri_complete")
                            or flow.get("verification_uri")
                            or DEVICE_LOGIN_URL)
        plain_uri = flow.get("verification_uri") or DEVICE_LOGIN_URL
        self._code_lbl.configure(text=self._code)
        self._steps.configure(
            text=(f"1. A browser is opening:  {plain_uri}\n"
                  f"2. Enter the code above and sign in as the mailbox account.\n"
                  f"3. Approve the permission request.\n\n"
                  f"Use THAT page, not any other Microsoft sign-in page - the "
                  f"code only works there. If the browser finishes on 'This is "
                  f"not the right page', that is normal; this window shows the "
                  f"real result."))
        # Copy/open first: both write to the status box, and the waiting
        # message must be the one left on screen.
        self._copy()
        self._open()
        self._say("Waiting for you to complete sign-in in the browser...\n\n"
                  f"Enter code {self._code} at:\n{plain_uri}\n\n" + report,
                  C["yellow"])

        # The worker only records the outcome; the Tk thread picks it up by
        # polling. Calling .after() from a worker thread is not reliably
        # thread-safe and can be dropped, which would leave this window stuck
        # on "Waiting..." forever.
        def work() -> None:
            """Worker thread: block on the sign-in, record the outcome."""
            try:
                who = complete_device_login(self._settings, flow, app, cache)
                log.info("Graph sign-in succeeded for %s", who)
                self._result = (f"SUCCESS - signed in as {who}.\n\n"
                                f"Close this window and click 'Test mailbox'.",
                                C["green"])
            except Exception as exc:
                log.error("Graph sign-in failed: %s", exc)
                self._result = (f"FAILED\n\n{exc}", C["red"])

        threading.Thread(target=work, daemon=True, name="graph-signin").start()
        self.after(300, self._poll_result)

    def _poll_result(self) -> None:
        """Main-thread poll for the worker's outcome."""
        if self._closed:
            return
        if self._result is None:
            self.after(300, self._poll_result)
            return
        msg, colour = self._result
        self._finish(msg, colour)

    def _finish(self, msg: str, colour: str) -> None:
        """Show the final outcome and notify the Settings tab."""
        if self._closed:
            return
        self._say(msg, colour)
        self._steps.configure(text="Sign-in finished - see Status below.")
        if self._on_done:
            try:
                self._on_done()
            except Exception:
                pass
