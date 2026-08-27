"""AI-assisted extraction of customer + job reference from an invoice.

Text is gathered from the email body and any PDF/DOCX attachment, then handed
to Gemini or Anthropic with a strict JSON-output prompt. A regex fallback runs
if no AI key is configured or the call fails, so the watcher still functions.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, asdict
from pathlib import Path

log = logging.getLogger(__name__)

_PROMPT = """You extract structured data from contractor/supplier invoices.
Return ONLY minified JSON with these keys:
  customer_name  - the CUSTOMER / client / bill-to company the invoice is for
  job_number     - job / work order number if present, else ""
  invoice_ref    - the invoice / credit note number, else ""
  amount_total   - total incl. tax as a number string, else ""
  invoice_date   - ISO date if present, else ""
  doc_type       - "credit" if this is a credit note / adjustment note / credit
                   memo / refund, otherwise "invoice"
  confidence     - 0..1 float, your confidence in customer_name
Do not include commentary. If unknown, use "".

--- EMAIL SUBJECT ---
{subject}
--- EMAIL BODY ---
{body}
--- ATTACHMENT TEXT ---
{attachment}
"""


@dataclass
class ParseResult:
    """Normalised extraction output."""

    customer_name: str = ""
    job_number: str = ""
    invoice_ref: str = ""
    amount_total: str = ""
    invoice_date: str = ""
    doc_type: str = "invoice"        # "invoice" | "credit"
    confidence: float = 0.0
    source: str = "regex"

    def as_dict(self) -> dict:
        return asdict(self)


# --------------------------------------------------------------------------
# Attachment text extraction
# --------------------------------------------------------------------------
def extract_text(path: Path, limit: int = 12000) -> str:
    """Best-effort plain-text extraction from a single attachment."""
    ext = path.suffix.lower().lstrip(".")
    try:
        if ext == "pdf":
            from pdfminer.high_level import extract_text as pdf_extract
            return (pdf_extract(str(path)) or "")[:limit]
        if ext == "docx":
            import docx
            doc = docx.Document(str(path))
            return "\n".join(p.text for p in doc.paragraphs)[:limit]
        if ext in ("csv", "txt"):
            return path.read_text(errors="ignore")[:limit]
    except Exception as exc:
        log.warning("Text extraction failed for %s: %s", path.name, exc)
    return ""


# --------------------------------------------------------------------------
# AI providers
# --------------------------------------------------------------------------
def _call_gemini(api_key: str, model: str, prompt: str) -> str:
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    resp = genai.GenerativeModel(model or "gemini-1.5-flash").generate_content(prompt)
    return resp.text or ""


def _call_anthropic(api_key: str, model: str, prompt: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=model or "claude-sonnet-5",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")


def _coerce_json(text: str) -> dict:
    """Pull the first JSON object out of a model response."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}


# --------------------------------------------------------------------------
# Regex fallback
# --------------------------------------------------------------------------
def _regex_fallback(subject: str, body: str, attachment: str) -> ParseResult:
    """Cheap heuristic extraction when AI is unavailable."""
    blob = f"{subject}\n{body}\n{attachment}"
    job = re.search(r"(?:job|work\s*order|wo|job\s*no\.?|job\s*#)\s*[:#]?\s*([A-Za-z0-9-]{3,})",
                    blob, re.I)
    inv = re.search(r"(?:invoice|inv)\s*(?:no\.?|number|#)?\s*[:#]?\s*([A-Za-z0-9-]{3,})",
                    blob, re.I)
    cust = re.search(r"(?:bill\s*to|customer|client|to)\s*[:\-]\s*(.+)", blob, re.I)
    is_credit = re.search(r"credit\s*note|adjustment\s*note|credit\s*memo|\brefund\b",
                          blob, re.I)
    return ParseResult(
        customer_name=(cust.group(1).splitlines()[0].strip() if cust else ""),
        job_number=(job.group(1) if job else ""),
        invoice_ref=(inv.group(1) if inv else ""),
        doc_type="credit" if is_credit else "invoice",
        confidence=0.2 if cust else 0.0,
        source="regex",
    )


class InvoiceParser:
    """Chooses a provider based on settings and produces a :class:`ParseResult`."""

    def __init__(self, settings) -> None:
        self._settings = settings

    def parse(self, subject: str, body: str, attachments: list[Path]) -> ParseResult:
        """Run extraction over one email + its attachments."""
        attachment_text = "\n\n".join(extract_text(p) for p in attachments)[:12000]
        provider = self._settings.get("ai.provider", "gemini")
        model = self._settings.get("ai.model", "")
        key = self._settings.get(
            "ai.gemini_api_key" if provider == "gemini" else "ai.anthropic_api_key"
        )

        if key:
            prompt = _PROMPT.format(subject=subject, body=body[:6000],
                                    attachment=attachment_text)
            try:
                raw = (_call_gemini if provider == "gemini" else _call_anthropic)(
                    key, model, prompt
                )
                data = _coerce_json(raw)
                if data:
                    return ParseResult(
                        customer_name=str(data.get("customer_name", "")).strip(),
                        job_number=str(data.get("job_number", "")).strip(),
                        invoice_ref=str(data.get("invoice_ref", "")).strip(),
                        amount_total=str(data.get("amount_total", "")).strip(),
                        invoice_date=str(data.get("invoice_date", "")).strip(),
                        doc_type=("credit" if str(data.get("doc_type", "")).strip().lower()
                                  .startswith("credit") else "invoice"),
                        confidence=float(data.get("confidence", 0) or 0),
                        source=provider,
                    )
            except Exception as exc:
                log.error("AI parse failed (%s); using regex fallback: %s", provider, exc)

        return _regex_fallback(subject, body, attachment_text)
