"""Shared provider contract for every external destination.

Two categories:
  * ``service``    - field-service / job-management systems (ServiceM8, simPRO,
                     AroFlo, ...). Invoices attach to a *job*.
  * ``accounting`` - accounting / bookkeeping systems (MYOB, Xero, QBO, ...).
                     Invoices attach to a *supplier bill*.

The watcher/router only ever talk to this interface. Adding a system means
writing one subclass and listing it in :mod:`integrations.registry`.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class UploadContext:
    """Everything a provider needs to file one invoice attachment."""

    customer_name: str
    customer_external_id: str       # per-customer mapping stored in the DB
    job_number: str
    invoice_ref: str
    amount_total: str
    invoice_date: str
    file_path: Path
    email_subject: str
    doc_type: str = "invoice"        # "invoice" | "credit"

    @property
    def is_credit(self) -> bool:
        return self.doc_type == "credit"


@dataclass
class UploadResult:
    """Outcome returned to the router / logs."""

    ok: bool
    platform: str
    detail: str
    remote_id: str = ""


class Provider:
    """Base class. Subclasses implement auth + upload for one system."""

    key: str = "base"
    label: str = "Base Provider"
    category: str = "accounting"        # "service" | "accounting"
    implemented: bool = True            # False -> shown as "(preview)" in the UI
    uses_oauth: bool = False            # True -> the Authorise button applies

    #: (setting_key, field_label, is_secret) - drives which inputs the UI shows
    setting_fields: list[tuple[str, str, bool]] = []

    def __init__(self, settings) -> None:
        self._settings = settings

    def configured(self) -> bool:
        """True when every mandatory setting for this provider is present."""
        return bool(self.setting_fields) and all(
            self._settings.get(k) for k, _, _ in self.setting_fields
        )

    def missing_fields(self) -> list[str]:
        """Human labels of the settings still blank."""
        return [lbl for k, lbl, _ in self.setting_fields if not self._settings.get(k)]

    def test_connection(self) -> UploadResult:
        raise NotImplementedError

    def upload_invoice(self, ctx: UploadContext) -> UploadResult:
        raise NotImplementedError


# Backwards-compatible alias (old imports).
AccountingProvider = Provider


class NoneProvider(Provider):
    """'None / disabled' entry for either dropdown."""

    key = "none"
    label = "None / Disabled"
    implemented = False
    setting_fields = []

    def configured(self) -> bool:
        return False

    def test_connection(self) -> UploadResult:
        return UploadResult(False, self.label, "No provider selected.")

    def upload_invoice(self, ctx: UploadContext) -> UploadResult:
        return UploadResult(False, self.label, "No provider selected.")


class StubProvider(Provider):
    """A selectable provider whose API client is not wired yet.

    It still advertises its real credential fields so the deployment can be
    configured now; uploads fail loudly (and land in the retry queue) until
    the concrete client is added.
    """

    implemented = False

    def test_connection(self) -> UploadResult:
        missing = self.missing_fields()
        if missing:
            return UploadResult(False, self.label, f"Missing: {', '.join(missing)}")
        return UploadResult(
            False, self.label,
            f"{self.label}: credentials look complete, but the upload client "
            f"is a preview and is not wired yet.",
        )

    def upload_invoice(self, ctx: UploadContext) -> UploadResult:
        return UploadResult(
            False, self.label,
            f"{self.label} upload is not implemented in this build.",
        )
