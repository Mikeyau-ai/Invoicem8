# Changelog

All notable changes to InvoiceM8. Newest first. Bump `version.py` and add an
entry here for every release.

## 1.0.5
- In-app **About / Changelog** window (click the InvoiceM8 wordmark in the
  header, or Settings > Updates > About / Changelog). Shows the version, a
  GitHub link, and this changelog, bundled so it works offline.

## 1.0.4
- Clean shutdown: close is now idempotent and exception-safe, cancels its
  scheduled callbacks, stops the watcher (bounded), then closes the database
  and the window in order. A late write from a worker thread on exit can no
  longer raise.

## 1.0.3
- The self-updater's swap step now runs in its **own visible console window**
  with an InvoiceM8 banner, the repo URL, a clear "not a background/malware
  process" note, step-by-step status, and a visible countdown that holds the
  window open long enough to read before it closes.
- Build/release scripts show the same banner.

## 1.0.2
- Version wiring: `version.py` is the single source of truth for the app
  version (shown in the title bar and Settings > Updates).

## 1.0.1
- Self-update system: frozen builds check GitHub Releases on launch (and via
  Settings > Updates > Check for updates now), download the new build, and
  swap it in. Auto-check is toggleable; running from source never prompts.

## 1.0.0
- First build. Outlook watcher (COM + Microsoft Graph), AI invoice parsing
  (OpenAI / Gemini / Anthropic / any OpenAI-compatible endpoint, all plain
  REST), local SQLite customer database with per-customer routing toggles.
- Pluggable Service systems (ServiceM8 wired; simPRO, AroFlo, Tradify, Fergus,
  Jobber, ServiceTitan, Housecall Pro as previews) and Accounting systems
  (Xero, MYOB, QuickBooks Online wired; Reckon, Sage, FreshBooks as previews),
  each selectable from Settings.
- Credit-note detection and routing; per-email and per-document duplicate
  guards so nothing is uploaded twice.
- Encrypted credential storage (Fernet key in Windows Credential Manager).
- Searchable activity log and a separate error log with manual retry.
- Per-field help popups and per-provider setup guides.
- "Run on Windows startup" toggle.
- Dark UI matching the RamBo desktop app.
