# Changelog

All notable changes to InvoiceM8. Newest first. Bump `version.py` and add an
entry here for every release.

## 1.0.10
- ServiceM8: authenticate with the `X-API-Key` header (the documented method
  for Private Application keys) instead of HTTP Basic auth. Basic auth made
  ServiceM8 reply "HTTP 401: Invalid username or password" on Test service.

## 1.0.9
- Update dialog: the "What's new" box now word-wraps (it was breaking
  mid-word) and uses bullet points.

## 1.0.8
- Update dialog: wrapped changelog bullets are joined back into one entry
  each, so "What's new" reads as a clean list instead of a spurious extra
  dash on every continuation line.

## 1.0.7
- Fixed the auto-update relaunch: the freshly-installed exe could fail to
  start with a "parent process has different executable" security error
  because it inherited PyInstaller's onefile environment variables. The
  updater now hands it a clean environment.
- Disabled UPX compression on the build - UPX-packed executables trip
  antivirus heuristics (AVG/Defender flagging the download).
- Release notes are now taken from CHANGELOG.md, so the in-app "What's new"
  shows the real change list instead of "First release."

## 1.0.6
- Activity Log: "Clear" is now two buttons - **Clear filter** (resets the
  search box, also on Esc) and **Clear log** (permanently deletes the stored
  activity history, with a confirmation). The error log is unaffected.

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
