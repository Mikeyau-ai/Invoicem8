"""Selectable service-system providers whose upload clients are previews.

Each advertises the real credential fields the platform uses, so a deployment
can be configured now. Uploads fail into the retry queue until the concrete
API client is added.
"""
from __future__ import annotations

from integrations.provider_base import StubProvider


class SimproProvider(StubProvider):
    key = "simpro"
    label = "simPRO"
    category = "service"
    uses_oauth = True
    setting_fields = [
        ("simpro.build_url", "Build URL (https://yourco.simprosuite.com)", False),
        ("simpro.client_id", "OAuth Client ID", True),
        ("simpro.client_secret", "OAuth Client Secret", True),
        ("simpro.company_id", "Company ID", False),
    ]


class ArofloProvider(StubProvider):
    key = "aroflo"
    label = "AroFlo"
    category = "service"
    setting_fields = [
        ("aroflo.api_key", "API Key", True),
        ("aroflo.api_secret", "API Secret", True),
        ("aroflo.org_encoded", "Org Encoded ID", True),
    ]


class TradifyProvider(StubProvider):
    key = "tradify"
    label = "Tradify"
    category = "service"
    uses_oauth = True
    setting_fields = [
        ("tradify.client_id", "Client ID", True),
        ("tradify.client_secret", "Client Secret", True),
        ("tradify.refresh_token", "OAuth Refresh Token", True),
    ]


class FergusProvider(StubProvider):
    key = "fergus"
    label = "Fergus"
    category = "service"
    setting_fields = [
        ("fergus.personal_access_token", "Personal Access Token", True),
    ]


class JobberProvider(StubProvider):
    key = "jobber"
    label = "Jobber"
    category = "service"
    uses_oauth = True
    setting_fields = [
        ("jobber.client_id", "App Client ID", True),
        ("jobber.client_secret", "App Client Secret", True),
        ("jobber.redirect_uri", "Redirect URI", False),
        ("jobber.refresh_token", "OAuth Refresh Token", True),
    ]


class ServiceTitanProvider(StubProvider):
    key = "servicetitan"
    label = "ServiceTitan"
    category = "service"
    setting_fields = [
        ("servicetitan.client_id", "Client ID", True),
        ("servicetitan.client_secret", "Client Secret", True),
        ("servicetitan.app_key", "App Key", True),
        ("servicetitan.tenant_id", "Tenant ID", False),
    ]


class HousecallProProvider(StubProvider):
    key = "housecallpro"
    label = "Housecall Pro"
    category = "service"
    setting_fields = [
        ("housecallpro.api_key", "API Key", True),
    ]


SERVICE_STUBS = [
    SimproProvider, ArofloProvider, TradifyProvider, FergusProvider,
    JobberProvider, ServiceTitanProvider, HousecallProProvider,
]
