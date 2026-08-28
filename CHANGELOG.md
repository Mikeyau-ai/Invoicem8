# Changelog

All notable changes to InvoiceM8. Newest first. Bump `version.py` and add an
entry here for every release.

## 1.0.25
- **Fixed "that code didn't work" at the sign-in page.** A device code is only
  redeemable at the verification URI belonging to the authority that issued
  it, but 1.0.19 hardcoded microsoft.com/devicelogin - so a code issued
  against /consumers (or any specific tenant) was correctly rejected there.
  The app now opens the URI MSAL returns, prefers the one-click
  verification_uri_complete when offered, and prints the exact URL and code in
  the copyable status box.

## 1.0.24
- The sign-in window now prints exactly what it is about to use - Client ID
  (masked, with a length/format check), tenant, authority and scopes - so a
  blank or mistyped Client ID is obvious instead of being guessed at from
  Microsoft's error pages.
- Sign-in now REFUSES to start when the Client ID is empty or not a 36-char
  GUID. Sending Microsoft a malformed client_id produced wildly misleading
  results, including a sign-in page that ended up putting the password in the
  URL. The app no longer lets that request be made.
- The same configuration summary is written to invoicem8.log.

## 1.0.23
- **Fixed silent credential loss.** If the local encryption key in Windows
  Credential Manager is lost or regenerated, every saved API key, client ID
  and password becomes unrecoverable - and previously they just read back as
  EMPTY while the fields still showed masked dots, so the app looked
  configured but failed with confusing errors from the remote service.
  Settings now shows a red warning naming exactly which credentials must be
  re-entered.
- The Graph "no Client ID" error now says when the value is saved but
  undecryptable, instead of implying the app registration is wrong.
- A newly generated master key is read straight back to confirm Credential
  Manager actually persisted it; if it did not, the app falls back to a local
  key file so secrets survive a restart rather than being orphaned each launch.

## 1.0.22
- Sign-in window gains a "Copy status text" button, and every sign-in outcome
  is written to %LOCALAPPDATA%\InvoiceM8\logs\invoicem8.log - so the exact
  Microsoft error can be reported without taking a screenshot.
- Fixed the sign-in result being dropped: the outcome was pushed to the UI
  from the worker thread, which is not reliably thread-safe and could leave
  the window stuck on "Waiting..." even after Microsoft had answered. The Tk
  thread now polls for the result instead.

## 1.0.21
- Microsoft sign-in now opens its own window instead of reporting through the
  Settings status box: the code is shown in large text with Copy and Open
  buttons, and the real outcome (SUCCESS with the account name, or FAILED with
  Microsoft's exact error) appears in a selectable box you can copy from.
- The window states plainly that the browser finishing on Microsoft's "This is
  not the right page" is that page's normal behaviour, and that this window -
  not the browser - shows whether sign-in actually worked.

## 1.0.20
- Graph setup guide now includes the step that was missing: personal Microsoft
  accounts require a redirect URI registered under Authentication > Add a
  platform > "Mobile and desktop applications" >
  https://login.microsoftonline.com/common/oauth2/nativeclient. Without it,
  device-code sign-in fails with "invalid_request: The provided request must
  include a 'redirect_uri' input parameter", even though device-code flow
  normally needs no redirect URI.
- The sign-in error message now detects that exact failure and tells you the
  fix instead of just echoing Microsoft's wording.

## 1.0.19
- Fixed Microsoft sign-in failing with "invalid_request: The provided request
  must include a 'redirect_uri' input parameter". The app was opening MSAL's
  verification_uri, which for personal Microsoft accounts resolves to an
  endpoint that rejects a plain visit; it now always opens
  microsoft.com/devicelogin.
- The sign-in code is shown in large text in the status box AND copied to your
  clipboard, with numbered instructions, instead of relying on the browser.
- Sign-in no longer raises in the background if you close Settings while it is
  still waiting.

## 1.0.18
- Graph guide: the "no directory" step now covers the exact wording the portal
  shows ("The ability to create applications outside of a directory has been
  deprecated") and warns that the M365 Developer Program route it offers needs
  a PAID Visual Studio Professional/Enterprise subscription, leaving the free
  Azure account as the practical option. Also notes that business Microsoft
  365 accounts already have a directory, so customer sites skip this entirely.

## 1.0.17
- Graph setup guide rewritten against the CURRENT portal: sign-in is at
  entra.microsoft.com (not portal.azure.com), and the account-type option is
  now labelled "Any Entra ID Tenant + Personal Microsoft accounts". Adds the
  "Allow public client flows" step that device-code sign-in requires, and
  tells you to check entra.microsoft.com first before assuming you need to
  sign up for Azure.

## 1.0.16
- **New IMAP backend** (Settings > Email > Backend = `imap`). Works with
  Gmail, Fastmail, Yahoo, iCloud, Zoho and most business/cPanel mail hosts
  using just a server name and an app password - no Azure, no app
  registration, no subscription. A provider preset fills in the server and
  port for you. Mail is read with BODY.PEEK so your messages are never marked
  as read, and only emails with attachments are queued.
- **Corrected Graph guidance.** Microsoft now restricts creating a new Entra
  tenant to paid customers, so the advice added in 1.0.15 (create a free
  directory) no longer works on its own: a personal Microsoft account has to
  sign up for a free Azure account first, which creates the directory. The
  guide now says so, and points at IMAP as the easier route where possible.
- "Test Outlook" is now "Test mailbox", and the section is titled "Email",
  since it covers three backends. COM and Graph are unchanged.

## 1.0.15
- Graph setup guide and the Client ID help now cover the "AADSTS16000 /
  Interaction required - your live.com account does not exist in tenant
  Microsoft Services" wall that personal Microsoft accounts hit at
  portal.azure.com, with the exact steps to create your own free Entra
  directory so App registrations becomes available.

## 1.0.14
- **Microsoft Graph sign-in rebuilt around the device-code flow.** It now
  needs only an Application (client) ID - no client secret, no tenant ID, no
  redirect URI. Click "Sign in to Microsoft" in Settings > Outlook, enter the
  short code at microsoft.com/devicelogin, and that's it. The sign-in is
  cached (encrypted) and refreshes itself.
  This matters because the new Outlook for Windows has no COM interface,
  classic Outlook needs a paid Microsoft 365 subscription, and Microsoft
  disabled app-password/IMAP access for personal Outlook accounts in
  September 2024 - Graph OAuth2 is the only remaining option for those users.
- The COM backend is unchanged and still the default for sites running classic
  desktop Outlook.
- Setup guide for the Graph backend rewritten as an exact click-path, and the
  COM guide now spells out when COM cannot work.
- Graph errors are reported properly (folder not found, HTTP status) instead
  of a bare exception, and the scan report notes that the filter requires an
  attachment.

## 1.0.13
- Settings: the action buttons (Save, Test service, Test accounting, Test
  Outlook, Authorise OAuth, Setup guide) and the status box are now pinned in
  a fixed footer instead of living at the bottom of the scrolling form, so
  they are always reachable no matter how long the form gets.
- The status area is a scrollable, selectable text box - long diagnostics wrap
  and can be copied. This also removes a resize feedback loop introduced in
  1.0.12 that could stop the Settings window scrolling.
- Settings window height adapts to the screen (and has a minimum size), so the
  footer is on-screen on smaller laptop displays.

## 1.0.12
- Settings status line now word-wraps and grows with the window, so long
  diagnostics (Test Outlook, connection errors) are fully readable instead of
  being cut off at the edge.
- Mailbox matching is much less brittle: the configured address is matched
  against account SMTP addresses, account display names and data-file names.
  When it still doesn't match, the message now LISTS the accounts Outlook
  actually has on that PC so you can paste the right one in.
- Scan report now includes how many items the folder holds in total, and says
  outright when the folder is empty or has nothing recent - which usually
  means the wrong mailbox is selected.

## 1.0.11
- Outlook COM: if `Outlook.Application` can't be reached (which is always the
  case with the NEW Outlook for Windows Store app - it has no COM interface)
  the error now says exactly that and points at the fix, instead of a raw
  "Invalid class string" COM code.
- Watcher: "no new invoice emails" now reports what was actually scanned -
  which account and folder, how many emails were in the window, how many were
  skipped as already-read, and how many had no matching attachment.
- Attachment file names are now preserved (each message gets its own cache
  folder) and passed to the parser. A file like `testco10160.pdf` alone is
  enough to identify customer "testco" and job 10160.
- COM first scan looks back 14 days instead of the entire mailbox.
- "Only process unread emails" now defaults to OFF - duplicates are prevented
  by message-id, so the read flag was an unnecessary way to miss invoices.
- Test Outlook reports the same scan detail and honours the unread toggle.

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
