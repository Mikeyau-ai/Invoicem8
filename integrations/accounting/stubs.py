"""Selectable accounting providers whose upload clients are previews.

Fields are the real credentials each platform uses; uploads fail into the
retry queue until the concrete API client is added.
"""
from __future__ import annotations

from integrations.provider_base import StubProvider


class ReckonProvider(StubProvider):
    """Reckon accounting platform (preview)."""

    key = "reckon"
    label = "Reckon"
    category = "accounting"
    uses_oauth = True
    setting_fields = [
        ("reckon.client_id", "Client ID", True),
        ("reckon.client_secret", "Client Secret", True),
        ("reckon.redirect_uri", "Redirect URI", False),
        ("reckon.book_id", "Book ID", False),
        ("reckon.refresh_token", "OAuth Refresh Token", True),
    ]


class SageProvider(StubProvider):
    """Sage Business Cloud accounting platform (preview)."""

    key = "sage"
    label = "Sage Business Cloud"
    category = "accounting"
    uses_oauth = True
    setting_fields = [
        ("sage.client_id", "Client ID", True),
        ("sage.client_secret", "Client Secret", True),
        ("sage.redirect_uri", "Redirect URI", False),
        ("sage.refresh_token", "OAuth Refresh Token", True),
    ]


class FreshBooksProvider(StubProvider):
    """FreshBooks accounting platform (preview)."""

    key = "freshbooks"
    label = "FreshBooks"
    category = "accounting"
    uses_oauth = True
    setting_fields = [
        ("freshbooks.client_id", "Client ID", True),
        ("freshbooks.client_secret", "Client Secret", True),
        ("freshbooks.account_id", "Account ID", False),
        ("freshbooks.refresh_token", "OAuth Refresh Token", True),
    ]


ACCOUNTING_STUBS = [ReckonProvider, SageProvider, FreshBooksProvider]
