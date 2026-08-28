"""Global paths and constants for InvoiceM8.

Everything the app persists lives under %LOCALAPPDATA%\\InvoiceM8 so the
project folder stays clean and the data survives a code update.
"""
from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "InvoiceM8"

# Base data directory (created on first run).
if os.name == "nt":
    _base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
else:  # allow running/tests on non-Windows
    _base = Path.home() / ".local" / "share"

DATA_DIR = _base / APP_NAME
DB_PATH = DATA_DIR / "invoicem8.sqlite3"
ATTACHMENT_CACHE = DATA_DIR / "attachments"
LOG_DIR = DATA_DIR / "logs"

# keyring service name under which the Fernet master key is stored (DPAPI-backed).
KEYRING_SERVICE = "InvoiceM8-master-key"
KEYRING_USERNAME = "fernet"

# Registry key used by the "Run on startup" toggle.
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE_NAME = APP_NAME

# Watcher defaults.
DEFAULT_POLL_MINUTES = 5
# How long a processed email's cached attachments are kept on disk. They are
# only needed while an upload might still be retried; see core.housekeeping.
CACHE_RETENTION_DAYS = 30
SUPPORTED_FILE_TYPES = ["pdf", "docx", "csv", "xlsx", "png", "jpg"]
DEFAULT_FILE_TYPES = ["pdf"]


def ensure_dirs() -> None:
    """Create all runtime directories. Safe to call repeatedly."""
    for d in (DATA_DIR, ATTACHMENT_CACHE, LOG_DIR):
        d.mkdir(parents=True, exist_ok=True)
