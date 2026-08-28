"""Typed access to application settings with transparent encryption.

Keys listed in :data:`SECRET_KEYS` are Fernet-encrypted at rest. Everything
else is stored as plain text (poll interval, chosen provider, etc.).
"""
from __future__ import annotations

from core.crypto import SecretBox
from core.database import Database

# Fields that must never touch disk unencrypted.
SECRET_KEYS = {
    "servicem8.api_key",
    "myob.client_id",
    "myob.client_secret",
    "myob.redirect_uri",
    "myob.cf_username",
    "myob.cf_password",
    "myob.refresh_token",
    "xero.client_id",
    "xero.client_secret",
    "xero.refresh_token",
    "qbo.client_id",
    "qbo.client_secret",
    "qbo.refresh_token",
    "qbo.realm_id",
    # accounting preview providers
    "reckon.client_id", "reckon.client_secret", "reckon.refresh_token",
    "sage.client_id", "sage.client_secret", "sage.refresh_token",
    "freshbooks.client_id", "freshbooks.client_secret", "freshbooks.refresh_token",
    # service systems
    "simpro.client_id", "simpro.client_secret",
    "aroflo.api_key", "aroflo.api_secret", "aroflo.org_encoded",
    "tradify.client_id", "tradify.client_secret", "tradify.refresh_token",
    "fergus.personal_access_token",
    "jobber.client_id", "jobber.client_secret", "jobber.refresh_token",
    "servicetitan.client_id", "servicetitan.client_secret", "servicetitan.app_key",
    "housecallpro.api_key",
    "outlook.app_password",
    "outlook.graph_client_id",
    "outlook.graph_client_secret",
    "outlook.graph_tenant_id",
    "outlook.graph_refresh_token",
    # MSAL device-code token cache - holds live refresh tokens, so encrypt it.
    "outlook.graph_token_cache",
    "imap.password",
    "ai.gemini_api_key",
    "ai.anthropic_api_key",
    "ai.openai_api_key",
    "ai.compat_api_key",
}

# Defaults for non-secret settings.
DEFAULTS = {
    "service.provider": "servicem8",      # servicem8 | simpro | aroflo | ... | none
    "accounting.provider": "none",        # xero | myob | qbo | reckon | ... | none
    "outlook.backend": "com",             # com | graph | imap
    "outlook.graph_tenant": "common",     # common | consumers | <tenant id>
    "imap.host": "",
    "imap.port": "993",
    "imap.username": "",
    "imap.folder": "INBOX",
    "imap.preset": "Gmail",
    "outlook.account": "",                # mailbox / UPN to monitor
    "outlook.folder": "Inbox",
    "ai.provider": "gemini",              # openai | gemini | anthropic | openai_compatible
    "ai.model": "",                       # blank -> provider default
    "ai.compat_base_url": "http://localhost:11434/v1",  # OpenAI-compatible endpoint
    "watcher.poll_minutes": "5",
    "watcher.unread_only": "0",   # dedupe is by message-id, not the read flag
    "watcher.autostart": "0",             # start watcher when app opens
    "app.run_on_startup": "0",
}


class Settings:
    """Load/save helper around the ``settings`` DB table."""

    def __init__(self, db: Database, box: SecretBox) -> None:
        self._db = db
        self._box = box

    def get(self, key: str, default: str | None = None) -> str:
        """Return a decrypted setting value (or the default)."""
        raw, enc = self._db.get_setting(key, "")
        if raw == "" and key not in self._explicitly_set():
            return default if default is not None else DEFAULTS.get(key, "")
        return self._box.decrypt(raw) if enc else raw

    def get_bool(self, key: str) -> bool:
        return self.get(key, DEFAULTS.get(key, "0")).strip() in ("1", "true", "True", "yes")

    def get_int(self, key: str, default: int = 0) -> int:
        try:
            return int(self.get(key, str(default)))
        except (TypeError, ValueError):
            return default

    def set(self, key: str, value: str) -> None:
        """Persist a setting, encrypting it if it is a known secret."""
        value = "" if value is None else str(value)
        if key in SECRET_KEYS:
            self._db.set_setting(key, self._box.encrypt(value), encrypted=True)
        else:
            self._db.set_setting(key, value, encrypted=False)

    def update(self, mapping: dict[str, str]) -> None:
        for k, v in mapping.items():
            self.set(k, v)

    def as_dict(self, keys: list[str]) -> dict[str, str]:
        """Bulk read used by the Settings tab to populate fields."""
        return {k: self.get(k) for k in keys}

    def _explicitly_set(self) -> set[str]:
        return set(self._db.all_settings().keys())
