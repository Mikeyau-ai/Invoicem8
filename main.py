"""InvoiceM8 entry point.

    python main.py              # normal launch
    python main.py --autostart  # used by the Windows "Run on startup" entry:
                                # starts minimised-ish with the watcher running
"""
from __future__ import annotations

import logging
import sys

import customtkinter as ctk

from config import LOG_DIR, DB_PATH, ensure_dirs
from core.crypto import SecretBox
from core.database import Database
from core.settings_store import Settings
from gui import theme
from gui.app import App


def _setup_logging() -> None:
    """File + console logging for diagnostics (separate from the in-app log)."""
    ensure_dirs()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "invoicem8.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main() -> None:
    _setup_logging()
    autostart = "--autostart" in sys.argv

    box = SecretBox()
    db = Database(DB_PATH)
    settings = Settings(db, box)

    theme.apply(ctk)
    app = App(db, settings, box, autostart=autostart)
    app.mainloop()


if __name__ == "__main__":
    main()
