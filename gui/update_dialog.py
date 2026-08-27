"""'Update available' dialog with an in-place download/apply flow."""
from __future__ import annotations

import threading

import customtkinter as ctk

from core import updater
from gui.theme import C, FONT_HEAD, FONT_UI, accent_button
from version import APP_VERSION


class UpdateDialog(ctk.CTkToplevel):
    """Offers an update; on 'Update now' downloads it and relaunches."""

    def __init__(self, master, info: updater.UpdateInfo) -> None:
        super().__init__(master)
        self._master = master
        self._info = info
        self._cancel = False

        self.title("InvoiceM8 - Update available")
        self.geometry("480x460")
        self.resizable(False, False)
        self.configure(fg_color=C["bg"])
        self.attributes("-topmost", True)
        self.after(300, lambda: self.attributes("-topmost", False))

        ctk.CTkLabel(self, text=f"Version {info.version} is available",
                     font=FONT_HEAD, text_color=C["green"]).pack(anchor="w", padx=20, pady=(18, 2))
        ctk.CTkLabel(self, text=f"You have {APP_VERSION}.  Download is "
                                f"{info.size_mb:.0f} MB.", font=FONT_UI,
                     text_color=C["dim"]).pack(anchor="w", padx=20)

        notes = ctk.CTkTextbox(self, font=FONT_UI, fg_color=C["row"],
                               text_color=C["text"], height=210)
        notes.pack(fill="both", expand=True, padx=20, pady=12)
        lines = info.note_lines() or ["(no release notes)"]
        notes.insert("1.0", "What's new:\n" + "\n".join(f"  - {l}" for l in lines))
        notes.configure(state="disabled")

        self._bar = ctk.CTkProgressBar(self)
        self._bar.set(0)
        self._status = ctk.CTkLabel(self, text="", font=FONT_UI, text_color=C["dim"])

        btns = ctk.CTkFrame(self, fg_color=C["bg"])
        btns.pack(fill="x", padx=20, pady=(0, 16))
        self._update_btn = accent_button(ctk, btns, "Update now", self._start,
                                         colour=C["green"])
        self._update_btn.pack(side="right", padx=(8, 0))
        accent_button(ctk, btns, "Later", self.destroy, colour=C["btn_off"]).pack(side="right")
        accent_button(ctk, btns, "Skip this version", self._skip,
                      colour=C["btn_off"]).pack(side="left")

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # -- actions --------------------------------------------------
    def _skip(self) -> None:
        updater.skip_version(self._info.version)
        self.destroy()

    def _on_close(self) -> None:
        self._cancel = True
        self.destroy()

    def _start(self) -> None:
        """Download on a worker thread, marshalling progress back to Tk."""
        self._update_btn.configure(state="disabled", text="Downloading...")
        self._bar.pack(fill="x", padx=20, pady=(0, 4))
        self._status.pack(anchor="w", padx=20, pady=(0, 8))
        threading.Thread(target=self._download_worker, daemon=True).start()

    def _download_worker(self) -> None:
        def progress(done: int, total: int) -> None:
            frac = (done / total) if total else 0
            self.after(0, lambda: (self._bar.set(frac),
                                   self._status.configure(
                                       text=f"{done // 1024 // 1024} / "
                                            f"{(total or self._info.size) // 1024 // 1024} MB")))

        path = updater.download(self._info, progress_cb=progress,
                                cancel=lambda: self._cancel)
        self.after(0, lambda: self._finish(path))

    def _finish(self, path) -> None:
        if not path:
            self._status.configure(text="Download failed - try again later.",
                                   text_color=C["red"])
            self._update_btn.configure(state="normal", text="Update now")
            return
        self._status.configure(text="Installing and restarting...", text_color=C["green"])
        if updater.apply(path):
            # Hand off to the detached swap script; we must exit now.
            self.after(400, self._master._on_close)
        else:
            self._status.configure(text="Could not launch the installer.",
                                   text_color=C["red"])
            self._update_btn.configure(state="normal", text="Update now")
