"""Microsoft Graph sign-in via the OAuth2 device-code flow.

Why device code: Outlook.com personal mailboxes dropped Basic Authentication
on 2024-09-16, so IMAP/app passwords no longer work and Graph OAuth2 is the
only route. The device-code flow needs only a **Client ID** - no client
secret and no tenant. The app registration does need 'Allow public client
flows' = Yes and a 'Mobile and desktop applications' redirect URI of
https://login.microsoftonline.com/common/oauth2/nativeclient: personal
Microsoft accounts reject the flow without one.

The MSAL token cache is persisted (encrypted) in the settings table, so the
user signs in once and the watcher refreshes silently from then on.
"""
from __future__ import annotations

import logging

log = logging.getLogger(__name__)

SCOPES = ["Mail.Read"]          # MSAL adds the Graph resource prefix itself
CACHE_KEY = "outlook.graph_token_cache"


def _authority(tenant: str) -> str:
    """Authority URL. 'common' covers personal + work accounts."""
    return f"https://login.microsoftonline.com/{(tenant or 'common').strip()}"


def _load_cache(settings):
    """Rehydrate the serialisable MSAL token cache from settings."""
    import msal

    cache = msal.SerializableTokenCache()
    blob = settings.get(CACHE_KEY, "")
    if blob:
        try:
            cache.deserialize(blob)
        except Exception:
            log.warning("Graph token cache unreadable; a new sign-in is needed.")
    return cache


def _save_cache(settings, cache) -> None:
    """Persist the cache only when MSAL says it changed."""
    if cache.has_state_changed:
        settings.set(CACHE_KEY, cache.serialize())


def _app(settings, cache):
    """Public (secret-less) MSAL client for the configured Client ID."""
    import msal

    client_id = settings.get("outlook.graph_client_id", "").strip()
    if not client_id:
        # A blank client ID also happens when the stored (encrypted) value can
        # no longer be decrypted, which is easy to mistake for a portal
        # misconfiguration - Microsoft returns baffling errors for an empty
        # client_id - so say both possibilities out loud.
        extra = ""
        try:
            if "outlook.graph_client_id" in settings.unreadable_secrets():
                extra = (" The value IS saved but can no longer be decrypted "
                         "(the local encryption key changed), so it reads as "
                         "empty. Re-enter it and click Save settings.")
        except Exception:
            pass
        raise RuntimeError(
            "No Graph Client ID configured." + extra +
            " Get one from entra.microsoft.com > Entra ID > App registrations "
            "> your app > Overview > Application (client) ID."
        )
    return msal.PublicClientApplication(
        client_id, authority=_authority(settings.get("outlook.graph_tenant", "common")),
        token_cache=cache,
    )


def signed_in_account(settings) -> str:
    """Username of the cached account, or '' when not signed in."""
    try:
        cache = _load_cache(settings)
        accounts = _app(settings, cache).get_accounts()
        return accounts[0].get("username", "") if accounts else ""
    except Exception:
        return ""


def sign_out(settings) -> None:
    """Forget the cached tokens; the next fetch will require a new sign-in."""
    settings.set(CACHE_KEY, "")


def begin_device_login(settings) -> tuple[dict, object, object]:
    """Start a device-code sign-in.

    Returns ``(flow, app, cache)``. ``flow['message']`` is the instruction to
    show the user ("go to microsoft.com/devicelogin and enter CODE"). Pass all
    three to :func:`complete_device_login`, which blocks until the user
    finishes - so call it on a worker thread.
    """
    cache = _load_cache(settings)
    app = _app(settings, cache)
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise RuntimeError(
            "Could not start Microsoft sign-in: "
            f"{flow.get('error_description') or flow}. Check the Client ID, and "
            "that the app registration has BOTH: 'Allow public client flows' = "
            "Yes, and a 'Mobile and desktop applications' platform with the "
            "redirect URI "
            "https://login.microsoftonline.com/common/oauth2/nativeclient "
            "(personal Microsoft accounts require that redirect URI even for "
            "device-code sign-in)."
        )
    return flow, app, cache


def complete_device_login(settings, flow, app, cache) -> str:
    """Block until the user completes sign-in. Returns their username."""
    result = app.acquire_token_by_device_flow(flow)
    if "access_token" not in result:
        detail = result.get("error_description") or result
        hint = ""
        if "redirect_uri" in str(detail):
            hint = (
                "  FIX: in the app registration go to Authentication > "
                "Add a platform > 'Mobile and desktop applications' and "
                "tick https://login.microsoftonline.com/common/oauth2/"
                "nativeclient, then Configure. Personal Microsoft accounts "
                "need that redirect URI registered even for device-code "
                "sign-in.")
        raise RuntimeError(f"Microsoft sign-in failed: {detail}{hint}")
    _save_cache(settings, cache)
    return (result.get("id_token_claims") or {}).get("preferred_username", "signed in")


def access_token(settings) -> str:
    """A valid Graph access token from the cache, refreshing silently.

    Raises with an actionable message when no cached account exists.
    """
    cache = _load_cache(settings)
    app = _app(settings, cache)
    accounts = app.get_accounts()
    if not accounts:
        raise RuntimeError(
            "Not signed in to Microsoft. Open Settings > Outlook and click "
            "'Sign in to Microsoft'.")
    result = app.acquire_token_silent(SCOPES, account=accounts[0])
    _save_cache(settings, cache)
    if not result or "access_token" not in result:
        raise RuntimeError(
            "Microsoft sign-in has expired. Open Settings > Outlook and click "
            "'Sign in to Microsoft' again.")
    return result["access_token"]


def config_report(settings) -> str:
    """Human-readable summary of exactly what sign-in will use.

    Printed in the sign-in window so a bad/blank/mistyped client ID is visible
    immediately instead of being inferred from Microsoft's error pages.
    """
    raw = settings.get("outlook.graph_client_id", "")
    cid = (raw or "").strip()
    tenant = (settings.get("outlook.graph_tenant", "") or "common").strip() or "common"

    if not cid:
        state = "EMPTY - nothing was read from settings"
    elif len(cid) != 36 or cid.count("-") != 4:
        state = f"SUSPICIOUS - {len(cid)} chars, expected a 36-char GUID: {cid!r}"
    else:
        state = f"{cid[:8]}...{cid[-4:]}  (36-char GUID, looks valid)"

    lines = [
        f"Client ID : {state}",
        f"Tenant    : {tenant}",
        f"Authority : {_authority(tenant)}",
        f"Scopes    : {', '.join(SCOPES)}",
    ]
    try:
        if "outlook.graph_client_id" in settings.unreadable_secrets():
            lines.append("WARNING   : the stored Client ID cannot be decrypted "
                         "- re-enter it and Save settings.")
    except Exception:
        pass
    return "\n".join(lines)
