"""MYOB AccountRight / MYOB Business provider.

Auth is OAuth2 (bearer) plus a company-file token:
  * Authorization: Bearer <access_token>       (refreshed from refresh_token)
  * x-myobapi-key: <client_id>
  * x-myobapi-version: v2
  * x-myobapi-cftoken: base64(cf_username:cf_password)

The one-time OAuth consent is done via :func:`authorize_interactive` (opens a
browser, user pastes the ``code`` back). After that the refresh token is
stored encrypted and used headlessly.

Upload: this attaches the invoice PsF to a Supplier Bill / Purchase. Because
MYOB's document model varies by product, ``upload_invoice`` creates a
Purchase/Bill draft referencing the invoice number and attaches the file via
the ``/Attachment`` endpoint. Verify field names against your company file.

Docs: https://developer.myob.com/api/accountright/v2/
"""
from __future__ import annotations

import base64
import webbrowser

import requests

from integrations.provider_base import Provider, UploadContext, UploadResult

AUTH_URL = "https://secure.myob.com/oauth2/account/authorize"
TOKEN_URL = "https://secure.myob.com/oauth2/v1/authorize"
API_ROOT = "https://api.myob.com/accountright"


class MyobProvider(Provider):
    key = "myob"
    category = "accounting"
    uses_oauth = True
    label = "MYOB"
    setting_fields = [
        ("myob.client_id", "Client ID (API Key)", True),
        ("myob.client_secret", "Client Secret", True),
        ("myob.redirect_uri", "Redirect URI", True),
        ("myob.cf_username", "Company File Username", True),
        ("myob.cf_password", "Company File Password", True),
        ("myob.company_file_id", "Company File ID (GUID)", False),
        ("myob.refresh_token", "OAuth Refresh Token", True),
    ]

    # -- OAuth ---------------------------------------------------------
    def authorize_interactive(self) -> str:
        """Open the consent page. Returns the URL the user should visit."""
        params = {
            "client_id": self._settings.get("myob.client_id"),
            "redirect_uri": self._settings.get("myob.redirect_uri"),
            "response_type": "code",
            "scope": "CompanyFile",
        }
        url = AUTH_URL + "?" + requests.compat.urlencode(params)
        webbrowser.open(url)
        return url

    def exchange_code(self, code: str) -> None:
        """Swap an auth code for tokens and persist the refresh token."""
        data = {
            "client_id": self._settings.get("myob.client_id"),
            "client_secret": self._settings.get("myob.client_secret"),
            "scope": "CompanyFile",
            "code": code.strip(),
            "redirect_uri": self._settings.get("myob.redirect_uri"),
            "grant_type": "authorization_code",
        }
        r = requests.post(TOKEN_URL, data=data, timeout=30)
        r.raise_for_status()
        self._settings.set("myob.refresh_token", r.json()["refresh_token"])

    def _access_token(self) -> str:
        """Refresh and return a bearer token."""
        data = {
            "client_id": self._settings.get("myob.client_id"),
            "client_secret": self._settings.get("myob.client_secret"),
            "refresh_token": self._settings.get("myob.refresh_token"),
            "grant_type": "refresh_token",
        }
        r = requests.post(TOKEN_URL, data=data, timeout=30)
        r.raise_for_status()
        payload = r.json()
        if payload.get("refresh_token"):
            self._settings.set("myob.refresh_token", payload["refresh_token"])
        return payload["access_token"]

    def _headers(self) -> dict:
        cf_token = base64.b64encode(
            f"{self._settings.get('myob.cf_username')}:{self._settings.get('myob.cf_password')}".encode()
        ).decode()
        return {
            "Authorization": f"Bearer {self._access_token()}",
            "x-myobapi-key": self._settings.get("myob.client_id"),
            "x-myobapi-version": "v2",
            "x-myobapi-cftoken": cf_token,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _cf_base(self) -> str:
        return f"{API_ROOT}/{self._settings.get('myob.company_file_id')}"

    # -- provider API -------------------------------------------------
    def test_connection(self) -> UploadResult:
        try:
            r = requests.get(f"{API_ROOT}/", headers=self._headers(), timeout=25)
            if r.status_code == 200:
                return UploadResult(True, self.label, "Authenticated with MYOB.")
            return UploadResult(False, self.label, f"HTTP {r.status_code}: {r.text[:200]}")
        except requests.RequestException as exc:
            return UploadResult(False, self.label, f"MYOB error: {exc}")

    def upload_invoice(self, ctx: UploadContext) -> UploadResult:
        """Attach the invoice/credit file to a supplier bill in the company file.

        MYOB models a supplier credit as a Bill with a negative total (there is
        no separate 'supplier credit note' resource in the AccountRight API),
        so a credit note is created as a negative-amount draft bill and clearly
        described. Review it in MYOB before applying.
        """
        try:
            headers = self._headers()
            base = self._cf_base()
            credit = ctx.is_credit

            total = ctx.amount_total or "0"
            if credit and not str(total).lstrip().startswith("-"):
                total = f"-{total}"

            # Locate an existing bill by number, else create a draft.
            flt = requests.utils.quote(f"Number eq '{ctx.invoice_ref}'")
            find = requests.get(f"{base}/Purchase/Bill/Item?$filter={flt}",
                                headers=headers, timeout=25)
            find.raise_for_status()
            items = find.json().get("Items", [])

            if items:
                bill_uid = items[0]["UID"]
            else:
                label = "Credit note import" if credit else "Invoice import"
                draft = {
                    "Supplier": {"Name": ctx.customer_name},
                    "Number": ctx.invoice_ref or None,
                    "Date": ctx.invoice_date or None,
                    "Lines": [{
                        "Type": "Transaction",
                        "Description": f"{label} - {ctx.email_subject}"[:255],
                        "Total": total,
                    }],
                }
                created = requests.post(f"{base}/Purchase/Bill/Item",
                                        headers=headers, json=draft, timeout=30)
                created.raise_for_status()
                bill_uid = created.headers.get("Location", "").rstrip("/").split("/")[-1]

            with ctx.file_path.open("rb") as fh:
                blob = base64.b64encode(fh.read()).decode()
            attach = {
                "Origin": "SupplierBill",
                "OwnerUID": bill_uid,
                "FileName": ctx.file_path.name,
                "FileContentBase64": blob,
            }
            up = requests.post(f"{base}/Attachment", headers=headers, json=attach, timeout=60)
            up.raise_for_status()
            noun = "credit (negative bill)" if credit else "bill"
            return UploadResult(True, self.label,
                                f"Attached {ctx.file_path.name} to MYOB {noun} {ctx.invoice_ref}.",
                                remote_id=bill_uid)
        except requests.RequestException as exc:
            return UploadResult(False, self.label, f"MYOB upload failed: {exc}")
