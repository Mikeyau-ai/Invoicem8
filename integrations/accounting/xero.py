"""Xero provider - files invoices as attachments on an Accounts Payable bill.

OAuth2 (Authorization Code + PKCE-less confidential client). One-time consent
via :func:`authorize_interactive`; thereafter the refresh token is used.

Docs: https://developer.xero.com/documentation/api/accounting/attachments
"""
from __future__ import annotations

import mimetypes
import webbrowser

import requests

from integrations.provider_base import Provider, UploadContext, UploadResult

AUTH_URL = "https://login.xero.com/identity/connect/authorize"
TOKEN_URL = "https://identity.xero.com/connect/token"
API = "https://api.xero.com/api.xro/2.0"


class XeroProvider(Provider):
    key = "xero"
    category = "accounting"
    uses_oauth = True
    label = "Xero"
    setting_fields = [
        ("xero.client_id", "Client ID", True),
        ("xero.client_secret", "Client Secret", True),
        ("xero.redirect_uri", "Redirect URI", False),
        ("xero.tenant_id", "Tenant ID", False),
        ("xero.refresh_token", "OAuth Refresh Token", True),
    ]
    SCOPES = "offline_access accounting.transactions accounting.attachments accounting.contacts"

    def authorize_interactive(self) -> str:
        params = {
            "response_type": "code",
            "client_id": self._settings.get("xero.client_id"),
            "redirect_uri": self._settings.get("xero.redirect_uri"),
            "scope": self.SCOPES,
            "state": "invoicem8",
        }
        url = AUTH_URL + "?" + requests.compat.urlencode(params)
        webbrowser.open(url)
        return url

    def exchange_code(self, code: str) -> None:
        r = requests.post(TOKEN_URL, data={
            "grant_type": "authorization_code",
            "code": code.strip(),
            "redirect_uri": self._settings.get("xero.redirect_uri"),
        }, auth=(self._settings.get("xero.client_id"),
                 self._settings.get("xero.client_secret")), timeout=30)
        r.raise_for_status()
        self._settings.set("xero.refresh_token", r.json()["refresh_token"])

    def _access_token(self) -> str:
        r = requests.post(TOKEN_URL, data={
            "grant_type": "refresh_token",
            "refresh_token": self._settings.get("xero.refresh_token"),
        }, auth=(self._settings.get("xero.client_id"),
                 self._settings.get("xero.client_secret")), timeout=30)
        r.raise_for_status()
        payload = r.json()
        self._settings.set("xero.refresh_token", payload["refresh_token"])
        return payload["access_token"]

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._access_token()}",
            "Xero-tenant-id": self._settings.get("xero.tenant_id"),
            "Accept": "application/json",
        }

    def test_connection(self) -> UploadResult:
        try:
            r = requests.get(f"{API}/Organisation", headers=self._headers(), timeout=25)
            return UploadResult(r.ok, self.label,
                                "Connected to Xero." if r.ok else f"HTTP {r.status_code}")
        except requests.RequestException as exc:
            return UploadResult(False, self.label, f"Xero error: {exc}")

    def upload_invoice(self, ctx: UploadContext) -> UploadResult:
        try:
            headers = self._headers()
            acct_code = self._settings.get("xero.default_account_code", "400")

            if ctx.is_credit:
                # Accounts-payable credit note (ACCPAYCREDIT).
                where = requests.utils.quote(
                    f'Type=="ACCPAYCREDIT" AND CreditNoteNumber=="{ctx.invoice_ref}"')
                found = requests.get(f"{API}/CreditNotes?where={where}", headers=headers, timeout=25)
                found.raise_for_status()
                existing = found.json().get("CreditNotes", [])
                if existing:
                    doc_id = existing[0]["CreditNoteID"]
                else:
                    body = {"CreditNotes": [{
                        "Type": "ACCPAYCREDIT",
                        "Contact": {"Name": ctx.customer_name},
                        "CreditNoteNumber": ctx.invoice_ref or None,
                        "Date": ctx.invoice_date or None,
                        "LineItems": [{
                            "Description": f"Imported credit: {ctx.email_subject}"[:250],
                            "Quantity": 1,
                            "UnitAmount": ctx.amount_total or 0,
                            "AccountCode": acct_code,
                        }],
                        "Status": "DRAFT",
                    }]}
                    made = requests.post(f"{API}/CreditNotes", headers=headers, json=body, timeout=30)
                    made.raise_for_status()
                    doc_id = made.json()["CreditNotes"][0]["CreditNoteID"]
                attach_url = f"{API}/CreditNotes/{doc_id}/Attachments/{ctx.file_path.name}"
                noun = "credit note"
            else:
                where = requests.utils.quote(
                    f'Type=="ACCPAY" AND InvoiceNumber=="{ctx.invoice_ref}"')
                found = requests.get(f"{API}/Invoices?where={where}", headers=headers, timeout=25)
                found.raise_for_status()
                invoices = found.json().get("Invoices", [])
                if invoices:
                    doc_id = invoices[0]["InvoiceID"]
                else:
                    body = {"Invoices": [{
                        "Type": "ACCPAY",
                        "Contact": {"Name": ctx.customer_name},
                        "InvoiceNumber": ctx.invoice_ref or None,
                        "Date": ctx.invoice_date or None,
                        "LineItems": [{
                            "Description": f"Imported: {ctx.email_subject}"[:250],
                            "Quantity": 1,
                            "UnitAmount": ctx.amount_total or 0,
                            "AccountCode": acct_code,
                        }],
                        "Status": "DRAFT",
                    }]}
                    made = requests.post(f"{API}/Invoices", headers=headers, json=body, timeout=30)
                    made.raise_for_status()
                    doc_id = made.json()["Invoices"][0]["InvoiceID"]
                attach_url = f"{API}/Invoices/{doc_id}/Attachments/{ctx.file_path.name}"
                noun = "bill"

            mime = mimetypes.guess_type(ctx.file_path.name)[0] or "application/pdf"
            with ctx.file_path.open("rb") as fh:
                up = requests.put(attach_url, headers={**headers, "Content-Type": mime},
                                  data=fh.read(), timeout=60)
            up.raise_for_status()
            return UploadResult(True, self.label,
                                f"Attached {ctx.file_path.name} to Xero {noun} {ctx.invoice_ref}.",
                                remote_id=doc_id)
        except requests.RequestException as exc:
            return UploadResult(False, self.label, f"Xero upload failed: {exc}")
