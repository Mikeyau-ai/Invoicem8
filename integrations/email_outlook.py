"""Outlook access with two interchangeable backends.

* ``com``   - local Outlook via pywin32 (works with the desktop client the
              user is already signed into; no cloud credentials needed).
* ``graph`` - Microsoft Graph REST API using MSAL refresh-token auth.

Both backends return a list of :class:`EmailMessage`; attachments are written
to the attachment cache and referenced by path.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config import ATTACHMENT_CACHE

log = logging.getLogger(__name__)

# On a fresh install (nothing processed yet) don't ingest the whole mailbox -
# only look this far back.
FIRST_SCAN_LOOKBACK_DAYS = 14


@dataclass
class EmailMessage:
    """Normalised representation of one inbox item."""

    message_id: str
    subject: str
    sender: str
    received_at: datetime
    body: str
    attachments: list[Path] = field(default_factory=list)
    is_unread: bool = True


def _safe(name: str) -> str:
    """Sanitise a filename for the local cache."""
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_") or "attachment"


class OutlookBackend:
    """Base interface. ``fetch`` is the only method the watcher calls."""

    #: human-readable summary of the last fetch, shown when it returns nothing
    last_scan: str = ""

    def fetch(self, since: datetime | None, unread_only: bool,
              allowed_ext: set[str]) -> list[EmailMessage]:
        raise NotImplementedError


# --------------------------------------------------------------------------
# COM backend
# --------------------------------------------------------------------------
class ComBackend(OutlookBackend):
    """Reads the local Outlook profile through the COM automation model."""

    def __init__(self, account: str = "", folder: str = "Inbox") -> None:
        self._account = (account or "").strip()
        self._folder = (folder or "").strip() or "Inbox"
        self.last_scan = ""

    def _inbox(self):
        """Resolve the target folder. Returns (folder, human_description)."""
        import win32com.client  # imported lazily so non-Windows import works

        try:
            outlook = win32com.client.Dispatch("Outlook.Application")
        except Exception as exc:
            # -2147221005 "Invalid class string" = Outlook.Application is not
            # registered. The NEW Outlook for Windows (the Store app) has no
            # COM automation interface at all, so this backend cannot work.
            raise RuntimeError(
                "Cannot reach the Outlook desktop app (COM). This usually means "
                "you have the NEW Outlook for Windows (the Microsoft Store app), "
                "which does not support COM automation. Either switch that app's "
                "'New Outlook' toggle OFF to use classic Outlook, or set "
                "Settings > Outlook > Backend to 'graph' and fill in the "
                f"Microsoft Graph fields. (underlying error: {exc})"
            ) from exc

        ns = outlook.GetNamespace("MAPI")
        note = ""

        if self._account:
            # Prefer an exact SMTP-address match on a configured account.
            try:
                for acct in ns.Accounts:
                    if (getattr(acct, "SmtpAddress", "") or "").lower() == self._account.lower():
                        store = acct.DeliveryStore
                        root = store.GetRootFolder()
                        f = self._find_folder(root, self._folder) or root.Folders["Inbox"]
                        return f, f"account '{acct.SmtpAddress}', folder '{f.Name}'"
            except Exception:
                pass
            # Fall back to a display-name substring match on the stores.
            for store in ns.Stores:
                dn = store.DisplayName or ""
                if self._account.lower() in dn.lower():
                    root = store.GetRootFolder()
                    f = self._find_folder(root, self._folder) or root.Folders["Inbox"]
                    return f, f"store '{dn}', folder '{f.Name}'"
            note = f"account '{self._account}' not matched to an Outlook account; using default. "

        inbox = ns.GetDefaultFolder(6)  # 6 = olFolderInbox
        if self._folder.lower() != "inbox":
            found = self._find_folder(inbox.Parent, self._folder)
            if found:
                return found, note + f"default account, folder '{found.Name}'"
            note += f"folder '{self._folder}' not found; using Inbox. "
        return inbox, note + "default account, Inbox"

    @staticmethod
    def _find_folder(root, name: str):
        """Depth-first search for a folder by display name."""
        try:
            for f in root.Folders:
                if (f.Name or "").lower() == name.lower():
                    return f
                sub = ComBackend._find_folder(f, name)
                if sub:
                    return sub
        except Exception:
            pass
        return None

    def fetch(self, since, unread_only, allowed_ext):
        import pywintypes  # noqa: F401  (ensures pywin32 present)

        inbox, where = self._inbox()
        # First run (no `since`): only look back a bounded window, not forever.
        floor = since or (datetime.now(timezone.utc)
                          - timedelta(days=FIRST_SCAN_LOOKBACK_DAYS))

        items = inbox.Items
        try:
            items.Sort("[ReceivedTime]", True)   # newest first
        except Exception:
            pass

        checked = older = read_skip = no_attach = 0
        results: list[EmailMessage] = []
        for idx, item in enumerate(items):
            if idx >= 1000:                       # hard cap on how far we scan
                break
            try:
                if getattr(item, "Class", 43) != 43:  # 43 = olMail
                    continue
                checked += 1
                received = item.ReceivedTime
                received_dt = datetime(
                    received.year, received.month, received.day,
                    received.hour, received.minute, received.second,
                    tzinfo=timezone.utc,
                )
                if received_dt <= floor:
                    older += 1
                    if older > 15:               # sorted desc - we're past the window
                        break
                    continue

                unread = bool(getattr(item, "UnRead", False))
                if unread_only and not unread:
                    read_skip += 1
                    continue

                saved: list[Path] = []
                # One sub-folder per message keeps the original file name clean
                # (the parser uses it as a hint) while staying collision-free.
                bucket = ATTACHMENT_CACHE / str(item.EntryID)[:24]
                for att in item.Attachments:
                    fname = _safe(att.FileName)
                    ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
                    if allowed_ext and ext not in allowed_ext:
                        continue
                    bucket.mkdir(parents=True, exist_ok=True)
                    dest = bucket / fname
                    att.SaveAsFile(str(dest))
                    saved.append(dest)

                if not saved:
                    no_attach += 1
                    continue

                results.append(EmailMessage(
                    message_id=str(item.EntryID),
                    subject=str(item.Subject or ""),
                    sender=str(getattr(item, "SenderEmailAddress", "") or ""),
                    received_at=received_dt,
                    body=str(item.Body or "")[:20000],
                    attachments=saved,
                    is_unread=unread,
                ))
            except Exception as exc:  # keep scanning other mail
                log.exception("COM item read failed: %s", exc)

        self.last_scan = (
            f"Scanned {where}. {checked} emails in window, "
            f"{read_skip} skipped as already-read (unread-only is "
            f"{'ON' if unread_only else 'off'}), "
            f"{no_attach} with no matching attachment, "
            f"{len(results)} queued for processing."
        )
        return results


# --------------------------------------------------------------------------
# Microsoft Graph backend
# --------------------------------------------------------------------------
class GraphBackend(OutlookBackend):
    """Cloud mailbox access via Graph. Requires a stored refresh token."""

    GRAPH = "https://graph.microsoft.com/v1.0"
    SCOPES = ["https://graph.microsoft.com/Mail.Read"]

    def __init__(self, tenant_id: str, client_id: str, client_secret: str,
                 refresh_token: str, account: str, folder: str = "Inbox") -> None:
        self._tenant = tenant_id
        self._client_id = client_id
        self._client_secret = client_secret
        self._refresh_token = refresh_token
        self._account = account
        self._folder = folder or "Inbox"
        self.last_scan = ""

    def _token(self) -> str:
        """Exchange the stored refresh token for an access token."""
        import msal

        app = msal.ConfidentialClientApplication(
            self._client_id,
            authority=f"https://login.microsoftonline.com/{self._tenant}",
            client_credential=self._client_secret,
        )
        result = app.acquire_token_by_refresh_token(self._refresh_token, scopes=self.SCOPES)
        if "access_token" not in result:
            raise RuntimeError(f"Graph auth failed: {result.get('error_description')}")
        return result["access_token"]

    def fetch(self, since, unread_only, allowed_ext):
        import requests

        headers = {"Authorization": f"Bearer {self._token()}"}
        base = f"{self.GRAPH}/users/{self._account}" if self._account else f"{self.GRAPH}/me"
        params = {
            "$top": "50",
            "$orderby": "receivedDateTime desc",
            "$select": "id,subject,from,receivedDateTime,isRead,bodyPreview,hasAttachments,body",
        }
        filters = ["hasAttachments eq true"]
        if unread_only:
            filters.append("isRead eq false")
        if since:
            filters.append(f"receivedDateTime ge {since.astimezone(timezone.utc).isoformat()}")
        params["$filter"] = " and ".join(filters)

        url = f"{base}/mailFolders/{self._folder}/messages"
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()

        value = resp.json().get("value", [])
        results: list[EmailMessage] = []
        for msg in value:
            received_dt = datetime.fromisoformat(
                msg["receivedDateTime"].replace("Z", "+00:00")
            )
            saved = self._download_attachments(base, msg["id"], headers, allowed_ext, requests)
            if not saved:
                continue
            results.append(EmailMessage(
                message_id=msg["id"],
                subject=msg.get("subject", ""),
                sender=(msg.get("from", {}).get("emailAddress", {}) or {}).get("address", ""),
                received_at=received_dt,
                body=(msg.get("body", {}) or {}).get("content", "")[:20000],
                attachments=saved,
                is_unread=not msg.get("isRead", True),
            ))
        self.last_scan = (
            f"Graph folder '{self._folder}' for "
            f"{self._account or 'the signed-in mailbox'}: filter [{params['$filter']}] "
            f"matched {len(value)} messages, {len(results)} with a usable attachment."
        )
        return results

    def _download_attachments(self, base, msg_id, headers, allowed_ext, requests):
        """Pull file attachments for one message into the local cache."""
        import base64

        url = f"{base}/messages/{msg_id}/attachments"
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        out: list[Path] = []
        for att in resp.json().get("value", []):
            if att.get("@odata.type") != "#microsoft.graph.fileAttachment":
                continue
            fname = _safe(att.get("name", "attachment"))
            ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
            if allowed_ext and ext not in allowed_ext:
                continue
            bucket = ATTACHMENT_CACHE / re.sub(r"[^A-Za-z0-9]", "", msg_id)[:24]
            bucket.mkdir(parents=True, exist_ok=True)
            dest = bucket / fname
            dest.write_bytes(base64.b64decode(att["contentBytes"]))
            out.append(dest)
        return out


def build_backend(settings) -> OutlookBackend:
    """Factory that returns the backend selected in Settings."""
    backend = settings.get("outlook.backend", "com")
    account = settings.get("outlook.account", "")
    folder = settings.get("outlook.folder", "Inbox")
    if backend == "graph":
        return GraphBackend(
            tenant_id=settings.get("outlook.graph_tenant_id"),
            client_id=settings.get("outlook.graph_client_id"),
            client_secret=settings.get("outlook.graph_client_secret"),
            refresh_token=settings.get("outlook.graph_refresh_token"),
            account=account,
            folder=folder,
        )
    return ComBackend(account=account, folder=folder)
