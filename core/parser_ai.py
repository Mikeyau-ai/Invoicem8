"""AI-assisted extraction of customer + job reference from an invoice.

Text is gathered from the email body and any PDF/DOCX attachment, then handed
to an LLM with a strict JSON-output prompt. A regex fallback runs if no AI key
is configured or the call fails, so the watcher still functions.

Every provider is called over its plain REST API with ``requests`` - no vendor
SDKs. Supported out of the box:

  * ``openai``            - OpenAI / ChatGPT  (api.openai.com)
  * ``gemini``            - Google Gemini     (generativelanguage.googleapis.com)
  * ``anthropic``         - Anthropic Claude  (api.anthropic.com)
  * ``openai_compatible`` - any OpenAI-compatible ``/chat/completions`` endpoint:
                            Azure OpenAI, OpenRouter, Groq, Together, Mistral,
                            DeepSeek, or a local server (Ollama, LM Studio,
                            llama.cpp, vLLM). Set the base URL in Settings.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, asdict
from pathlib import Path

import requests

log = logging.getLogger(__name__)

_PROMPT = """You extract structured data from contractor/supplier invoices.
Return ONLY minified JSON with these keys:
  customer_name  - the CUSTOMER / client / bill-to company the invoice is for
  job_number     - job / work order number if present, else ""
  invoice_ref    - the invoice / credit note number, else ""
  amount_total   - total incl. tax as a number string, else ""
  invoice_date   - ISO date if present, else ""
  doc_type       - "credit" if this is a CREDIT of any kind (credit note,
                   credit memo, adjustment note, credit invoice, refund),
                   otherwise "invoice". The word "credit" is the deciding
                   signal - but ignore ordinary payment wording such as
                   "credit card", "credit terms" or "credit limit", which
                   appears on normal invoices.
  confidence     - 0..1 float, your confidence in customer_name
Do not include commentary. If unknown, use "".

Suppliers label these fields inconsistently. Treat all of these as the
INVOICE reference: "Invoice No/Number/#/ID", "Tax Invoice", "Inv", "Bill No",
"Document No", "Statement No", "Our Ref", "Your Ref", "Reference".
Treat all of these as the JOB number: "Job", "Job No/Number/Ref", "Work
Order", "W/O", "Service Order", "Service Call", "Ticket", "Order No",
"Purchase Order"/"PO". If both a job number and a purchase order appear,
prefer the one labelled as a job.

The ATTACHMENT FILE NAMES are a strong hint: invoice PDFs are often named
like "Customer10160.pdf", "INV-1042_Customer.pdf" or "10160 Testco.pdf" - a
run of letters is usually the customer and a run of 3+ digits is usually the
job number or invoice number. Use them when the text is sparse or scanned.

--- EMAIL SUBJECT ---
{subject}
--- ATTACHMENT FILE NAMES ---
{filenames}
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
# AI providers (all plain REST)
# --------------------------------------------------------------------------
#: provider_key -> UI/behaviour metadata. `key_setting` is the settings key
#: holding that provider's API key; `needs_key` is False for local servers.
AI_PROVIDERS: dict[str, dict] = {
    "openai": {
        "label": "OpenAI (ChatGPT)",
        "key_setting": "ai.openai_api_key",
        "default_model": "gpt-4o-mini",
        "needs_key": True,
        "needs_base_url": False,
    },
    "gemini": {
        "label": "Google Gemini",
        "key_setting": "ai.gemini_api_key",
        "default_model": "gemini-1.5-flash",
        "needs_key": True,
        "needs_base_url": False,
    },
    "anthropic": {
        "label": "Anthropic (Claude)",
        "key_setting": "ai.anthropic_api_key",
        "default_model": "claude-sonnet-5",
        "needs_key": True,
        "needs_base_url": False,
    },
    "openai_compatible": {
        "label": "OpenAI-compatible (Azure / OpenRouter / Groq / Ollama / ...)",
        "key_setting": "ai.compat_api_key",
        "default_model": "",
        "needs_key": False,
        "needs_base_url": True,
    },
}

_HTTP_TIMEOUT = 45


def _post(url: str, headers: dict, payload: dict) -> dict:
    """POST JSON, raise for HTTP errors, return the decoded body."""
    resp = requests.post(url, headers={"Content-Type": "application/json", **headers},
                         json=payload, timeout=_HTTP_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _call_openai_chat(api_key: str, model: str, prompt: str,
                      base_url: str = "https://api.openai.com/v1") -> str:
    """OpenAI /chat/completions - also used for every OpenAI-compatible host."""
    base_url = (base_url or "https://api.openai.com/v1").rstrip("/")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    body = {
        "model": model or "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
    }
    try:
        data = _post(f"{base_url}/chat/completions", headers, body)
    except requests.HTTPError as exc:
        # Some compatible servers reject response_format - retry without it.
        if exc.response is not None and exc.response.status_code == 400:
            body.pop("response_format", None)
            data = _post(f"{base_url}/chat/completions", headers, body)
        else:
            raise
    return data["choices"][0]["message"]["content"] or ""


def _call_gemini(api_key: str, model: str, prompt: str) -> str:
    """Google Generative Language API - generateContent."""
    model = model or "gemini-1.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    data = _post(url, {"x-goog-api-key": api_key}, {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"response_mime_type": "application/json", "temperature": 0},
    })
    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts)


def _call_anthropic(api_key: str, model: str, prompt: str) -> str:
    """Anthropic Messages API."""
    data = _post("https://api.anthropic.com/v1/messages", {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }, {
        "model": model or "claude-sonnet-5",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    })
    return "".join(b.get("text", "") for b in data.get("content", [])
                   if b.get("type") == "text")


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
def _from_filename(names: str) -> tuple[str, str]:
    """Pull (customer, number) from a filename like 'testco10160.pdf' or
    '10160 Testco.pdf' / 'INV-1042_Acme.pdf'. Returns ('', '') if nothing fits."""
    for raw in names.splitlines():
        stem = re.sub(r"\.(pdf|docx?|csv|xlsx?|png|jpe?g)$", "", raw.strip(), flags=re.I)
        stem = re.sub(r"\b(inv(oice)?|invoice|bill)\b", " ", stem, flags=re.I)
        letters = re.search(r"[A-Za-z][A-Za-z&' ]{1,}[A-Za-z]", stem)
        digits = re.search(r"\d{3,}", stem)
        if letters or digits:
            name = re.sub(r"[_\-]+", " ", letters.group(0)).strip() if letters else ""
            return name, (digits.group(0) if digits else "")
    return "", ""


#: Phrases where "credit" is ordinary invoice wording, not a credit note -
#: e.g. "payment by credit card", "credit terms 30 days", "credit limit".
_CREDIT_FALSE_FRIENDS = re.compile(
    r"\bcredit\s*(?:card|limit|terms?|account|application|check|rating|"
    r"control|hold|balance|facility|score|union|available)\b", re.I)

#: Unambiguous credit-document wording.
_CREDIT_STRONG = re.compile(
    r"\bcredit\s*(?:note|memo|invoice|adjustment|advice)\b"
    r"|\badjustment\s*note\b"
    r"|\bcredit\s*not[ei]\b"
    r"|\brefund\b"
    r"|\bRCTI\s*credit\b", re.I)


def _looks_like_credit(blob: str) -> bool:
    """True when the document is a credit rather than an invoice.

    "Credit" is the one label that stays consistent across suppliers, so treat
    it as the deciding signal - but only after removing the phrases where
    "credit" is just payment wording on a normal invoice.
    """
    if _CREDIT_STRONG.search(blob):
        return True
    # Plain "credit" still counts, once the false friends are stripped out.
    cleaned = _CREDIT_FALSE_FRIENDS.sub(" ", blob)
    return bool(re.search(r"\bcredits?\b", cleaned, re.I))


def _regex_fallback(subject: str, body: str, attachment: str,
                    filenames: str = "") -> ParseResult:
    """Cheap heuristic extraction when AI is unavailable."""
    blob = f"{subject}\n{body}\n{attachment}\n{filenames}"
    # \b anchors stop "Invoice" itself being consumed as "inv" + "oice", and
    # the label words are skipped so "Job Reference: 10160" yields 10160 rather
    # than the word "Reference".
    # Trade invoices label these fields inconsistently, so match a broad
    # vocabulary rather than one phrasing. Ordered most- to least-specific:
    # an explicit "Job No" should win over a generic "Reference".
    _SEP = r"[\s.:#=\-]{0,4}"
    # A reference always contains a digit; allow an alpha prefix (INV-1042),
    # slashes and hyphens (WO/2026-14).
    _VALUE = r"([A-Za-z]{0,5}[-/ ]?\d[A-Za-z0-9\-/]*)"

    _JOB_LABELS = [
        r"job\s*(?:no|number|num|id|ref(?:erence)?|#)",
        r"\bjob\b",
        r"work\s*order\s*(?:no|number|num|#)?",
        r"\bw[/.]?o\b\s*(?:no|number|#)?",
        r"service\s*(?:order|call|ticket|job)\s*(?:no|number|#)?",
        r"ticket\s*(?:no|number|#)?",
        r"(?:purchase\s*order|\bp[./]?o\b)\s*(?:no|number|num|#)?",
        r"order\s*(?:no|number|num|#)",
        r"site\s*ref(?:erence)?\s*(?:no|number|#)?",
    ]
    _INV_LABELS = [
        r"tax\s*invoice\s*(?:no|number|num|id|#)?",
        r"credit\s*note\s*(?:no|number|num|#)?",
        r"invoice\s*(?:no|number|num|id|#)",
        r"\binvoice\b",
        r"\binv\b\s*(?:no|number|#)?",
        r"bill\s*(?:no|number|num|#)",
        r"(?:document|doc)\s*(?:no|number|num|#)",
        r"statement\s*(?:no|number|#)",
        r"(?:our|your|customer|client)\s*ref(?:erence)?\s*(?:no|number|#)?",
        r"\bref(?:erence)?\b\s*(?:no|number|#)?",
    ]

    def _find_labelled(labels: list[str]) -> str:
        """First value whose label matches, trying labels in priority order."""
        for label in labels:
            for m in re.finditer(label + _SEP + _VALUE, blob, re.I):
                value = m.group(1).strip(" -/")
                if any(ch.isdigit() for ch in value):
                    return value
        return ""

    job_number = _find_labelled(_JOB_LABELS)
    invoice_ref = _find_labelled(_INV_LABELS)
    cust = re.search(r"(?:bill\s*to|customer|client|to)\s*[:\-]\s*(.+)", blob, re.I)
    is_credit = _looks_like_credit(blob)

    fn_name, fn_num = _from_filename(filenames)
    customer = (cust.group(1).splitlines()[0].strip() if cust else "") or fn_name
    job_number = job_number or fn_num
    return ParseResult(
        customer_name=customer,
        job_number=job_number,
        invoice_ref=invoice_ref,
        doc_type="credit" if is_credit else "invoice",
        confidence=0.5 if (customer and job_number) else (0.2 if customer else 0.0),
        source="regex+filename" if (fn_name or fn_num) else "regex",
    )


class InvoiceParser:
    """Chooses a provider based on settings and produces a :class:`ParseResult`."""

    def __init__(self, settings) -> None:
        self._settings = settings

    def parse(self, subject: str, body: str, attachments: list[Path]) -> ParseResult:
        """Run extraction over one email + its attachments."""
        attachment_text = "\n\n".join(extract_text(p) for p in attachments)[:12000]
        filenames = "\n".join(p.name for p in attachments)
        provider = self._settings.get("ai.provider", "gemini")
        meta = AI_PROVIDERS.get(provider, AI_PROVIDERS["gemini"])
        model = self._settings.get("ai.model", "")
        key = self._settings.get(meta["key_setting"])
        base_url = self._settings.get("ai.compat_base_url")

        # Local / compatible servers may not need a key; everyone else does.
        if key or not meta["needs_key"]:
            prompt = _PROMPT.format(subject=subject, body=body[:6000],
                                    attachment=attachment_text, filenames=filenames)
            try:
                if provider == "openai":
                    raw = _call_openai_chat(key, model, prompt)
                elif provider == "openai_compatible":
                    raw = _call_openai_chat(key, model, prompt, base_url)
                elif provider == "anthropic":
                    raw = _call_anthropic(key, model, prompt)
                else:
                    raw = _call_gemini(key, model, prompt)
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

        return _regex_fallback(subject, body, attachment_text, filenames)
