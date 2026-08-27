# InvoiceM8

Local Windows desktop app that watches an Outlook inbox for invoice emails,
uses an AI parser to pull the **customer name** and **job / invoice reference**,
matches the customer against a local SQLite database, and pushes the attachment
to **ServiceM8** and/or an accounting system (**MYOB, Xero, QuickBooks Online**,
selectable per deployment).

Styled to match the RamBo desktop utility (same near-black palette, Segoe UI /
Consolas type, flat accent buttons).

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Python 3.11+ recommended. Windows only (uses pywin32 COM + `winreg`).

## First run

1. **Settings tab** – choose the accounting system, enter credentials, save.
   Secrets are encrypted with a Fernet key held in Windows Credential Manager
   (DPAPI). Nothing is stored in plain text.
2. For MYOB / Xero / QuickBooks click **Authorise OAuth provider** once to get a
   refresh token.
3. **Customers tab** – add customers and set their routing toggles.
4. Press **Start watcher** (or enable auto-start in Settings).

## Data location

`%LOCALAPPDATA%\InvoiceM8\` – `invoicem8.sqlite3`, `attachments\`, `logs\`.

## Module map

| Area      | Files |
|-----------|-------|
| Entry     | `main.py`, `config.py` |
| Security  | `core/crypto.py`, `core/settings_store.py` |
| Database  | `core/database.py` |
| Email     | `integrations/email_outlook.py` (COM + Graph) |
| AI parse  | `core/parser_ai.py` (Gemini / Anthropic + regex fallback) |
| Routing   | `core/router.py`, `core/watcher.py` |
| Providers | `integrations/accounting/*` + `registry.py` |
| Startup   | `core/startup.py` (HKCU Run key) |
| GUI       | `gui/*` (CustomTkinter, RamBo theme in `gui/theme.py`) |

## Caveats

- ServiceM8 / MYOB / Xero / QBO endpoints are implemented to their public docs
  but **field names and the exact bill/attachment model vary by account** –
  test against a sandbox company file before production use.
- Graph backend needs an Azure app registration with `Mail.Read`.
