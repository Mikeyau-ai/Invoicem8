"""ServiceM8 provider - attaches invoices to jobs via the REST API.

Auth: ServiceM8 "Private Application" API key sent as HTTP Basic
(``<api_key>:x`` base64) or the ``X-Api-Key`` header. We use the API key as
the basic-auth username which ServiceM8 accepts for private apps.

Flow:
  1. Look up the job by the extracted job number (``generated_job_id`` /
     ``job_number`` field on the Job object).
  2. Create an Attachment record linked to that job UUID and upload the file
     bytes to the ``.file`` sub-resource.

Docs: https://developer.servicem8.com/
"""
from __future__ import annotations

import base64
import mimetypes

import requests

from integrations.provider_base import Provider, UploadContext, UploadResult

API = "https://api.servicem8.com/api_1.0"


class ServiceM8Provider(Provider):
    key = "servicem8"
    label = "ServiceM8"
    category = "service"
    setting_fields = [("servicem8.api_key", "Private App API Key", True)]

    def _headers(self) -> dict:
        token = base64.b64encode(f"{self._settings.get('servicem8.api_key')}:x".encode()).decode()
        return {"Authorization": f"Basic {token}", "Accept": "application/json"}

    def test_connection(self) -> UploadResult:
        try:
            r = requests.get(f"{API}/job.json?%24top=1", headers=self._headers(), timeout=20)
            if r.status_code == 200:
                return UploadResult(True, self.label, "Connected to ServiceM8.")
            return UploadResult(False, self.label, f"HTTP {r.status_code}: {r.text[:200]}")
        except requests.RequestException as exc:
            return UploadResult(False, self.label, f"Connection error: {exc}")

    def _find_job_uuid(self, job_number: str) -> str | None:
        """Resolve a human job number to a ServiceM8 job UUID."""
        if not job_number:
            return None
        filt = requests.utils.quote(f"generated_job_id eq '{job_number}'")
        r = requests.get(f"{API}/job.json?%24filter={filt}", headers=self._headers(), timeout=20)
        r.raise_for_status()
        rows = r.json()
        if not rows:
            # Fall back to the internal sequential job_number field.
            filt2 = requests.utils.quote(f"job_number eq '{job_number}'")
            r = requests.get(f"{API}/job.json?%24filter={filt2}", headers=self._headers(), timeout=20)
            r.raise_for_status()
            rows = r.json()
        return rows[0]["uuid"] if rows else None

    def upload_invoice(self, ctx: UploadContext) -> UploadResult:
        try:
            job_uuid = self._find_job_uuid(ctx.job_number)
            if not job_uuid:
                return UploadResult(
                    False, self.label,
                    f"No ServiceM8 job found for job number '{ctx.job_number}'.",
                )

            fname = ctx.file_path.name
            mime = mimetypes.guess_type(fname)[0] or "application/pdf"
            # ServiceM8 stores a flat attachment on the job; flag credits in the
            # visible name so they are obvious in the job file.
            display_name = f"CREDIT NOTE - {fname}" if ctx.is_credit else fname

            # 1. create the attachment record
            meta = {
                "related_object": "job",
                "related_object_uuid": job_uuid,
                "attachment_name": display_name,
                "file_type": "." + fname.rsplit(".", 1)[-1].lower(),
                "active": 1,
            }
            r = requests.post(f"{API}/attachment.json", headers=self._headers(),
                              json=meta, timeout=30)
            r.raise_for_status()
            att_uuid = r.headers.get("x-record-uuid") or r.json().get("uuid", "")
            if not att_uuid:
                return UploadResult(False, self.label, "ServiceM8 did not return an attachment UUID.")

            # 2. upload the bytes
            with ctx.file_path.open("rb") as fh:
                up = requests.post(
                    f"{API}/attachment/{att_uuid}.file",
                    headers={**self._headers(), "Content-Type": mime},
                    data=fh.read(), timeout=60,
                )
            up.raise_for_status()
            return UploadResult(True, self.label,
                                f"Attached {fname} to job {ctx.job_number}.",
                                remote_id=att_uuid)
        except requests.RequestException as exc:
            return UploadResult(False, self.label, f"ServiceM8 API error: {exc}")
