"""Help text for the Settings tab.

* :data:`FIELD_HELP`  - one/two lines shown by the little ``?`` beside a row.
* :data:`SETUP_GUIDES` - step-by-step "where do I get these" per provider,
  shown by the "Setup guide" button in each section header and by the
  Help tab.

Nothing here is secret; it is just navigation help for each vendor portal.
Portal names/paths were accurate at build time - vendors move menus around,
so treat the paths as a strong hint rather than gospel.
"""
from __future__ import annotations

FIELD_HELP: dict[str, str] = {
    # -- ServiceM8 --
    "servicem8.api_key":
        "ServiceM8 > top-right menu > Add-ons > 'For Developers' > Create a "
        "Private Application. Copy the API Key it shows. Needs a plan tier that "
        "allows API access.",
    # -- simPRO --
    "simpro.build_url":
        "Your simPRO address, e.g. https://yourcompany.simprosuite.com "
        "(the URL you log in at).",
    "simpro.client_id":
        "simPRO > System > Setup > Utilities > API Access (or 'Integrations'). "
        "Create an OAuth2 client and copy the Client ID.",
    "simpro.client_secret":
        "Shown once when you create the OAuth2 client in simPRO API Access. "
        "Regenerate there if lost.",
    "simpro.company_id":
        "simPRO API is per-company. Find the numeric Company ID under "
        "System > Companies, or call GET /api/v1.0/companies/.",
    # -- AroFlo --
    "aroflo.api_key":
        "AroFlo > Site Administration > Integrations > AroFlo API. API access "
        "must be switched on by AroFlo support first.",
    "aroflo.api_secret":
        "Issued alongside the API Key on the AroFlo API integration page.",
    "aroflo.org_encoded":
        "The 'Organisation Encoded' string on the same AroFlo API page - "
        "identifies your org in signed requests.",
    # -- Tradify --
    "tradify.client_id":
        "Tradify API is partner-access only. Request credentials at "
        "tradify.com/integrations or email api@tradify.com; they issue a "
        "Client ID.",
    "tradify.client_secret":
        "Issued with the Client ID by the Tradify integrations team.",
    "tradify.refresh_token":
        "Filled automatically after you complete 'Authorise OAuth' once.",
    # -- Fergus --
    "fergus.personal_access_token":
        "Fergus > your avatar > Settings > Fergus API (or Developer). Generate "
        "a Personal Access Token. Ask Fergus support to enable API if you "
        "don't see the menu.",
    # -- Jobber --
    "jobber.client_id":
        "developer.getjobber.com > sign in > Apps > New App. Copy the Client ID.",
    "jobber.client_secret":
        "Shown with the Client ID in the Jobber Developer Center app settings.",
    "jobber.redirect_uri":
        "Any URL you control that you also enter in the Jobber app's 'Redirect "
        "URIs'. e.g. http://localhost:8765/callback",
    "jobber.refresh_token":
        "Filled automatically after you complete 'Authorise OAuth' once.",
    # -- ServiceTitan --
    "servicetitan.client_id":
        "developer.servicetitan.io > Applications > create app, then have your "
        "ServiceTitan admin approve it in Settings > Integrations > API "
        "Application Access. Client ID is on the app page.",
    "servicetitan.client_secret":
        "Generated on the ServiceTitan developer app page next to the Client ID.",
    "servicetitan.app_key":
        "The 'ST-App-Key' shown after your admin grants the app access to your "
        "tenant.",
    "servicetitan.tenant_id":
        "Your ServiceTitan account (tenant) ID - shown in the integration "
        "approval screen and in the API docs 'Try it' console.",
    # -- Housecall Pro --
    "housecallpro.api_key":
        "Housecall Pro > Settings > API & Integrations (Max plan) - generate an "
        "API key, or request one from Housecall Pro support.",

    # -- Xero --
    "xero.client_id":
        "developer.xero.com > My Apps > New app (choose 'Web app'). After "
        "creating it, open 'Configuration' - Client id is there.",
    "xero.client_secret":
        "Same Xero app > Configuration > 'Generate a secret'. Copy it "
        "immediately.",
    "xero.redirect_uri":
        "Add a redirect URI in the Xero app config and paste the same value "
        "here, e.g. http://localhost:8765/callback",
    "xero.tenant_id":
        "The organisation's tenant id. After 'Authorise OAuth', call "
        "GET https://api.xero.com/connections - use the 'tenantId'. Leave blank "
        "and re-test to have it hinted in the logs.",
    "xero.refresh_token":
        "Filled automatically after you complete 'Authorise OAuth' once.",
    # -- MYOB --
    "myob.client_id":
        "my.myob.com.au > Developer (developer.myob.com) > Register a new app. "
        "'API Key' = Client ID.",
    "myob.client_secret":
        "Shown with the API Key on the MYOB developer app page.",
    "myob.redirect_uri":
        "Must exactly match the 'Redirect URL' set on the MYOB developer app, "
        "e.g. http://localhost:8765/callback",
    "myob.company_file_id":
        "The company file GUID. Call GET https://api.myob.com/accountright/ "
        "after auth - use the file's 'Id'.",
    "myob.cf_username":
        "The user name you use to sign in to that MYOB company file "
        "(company-file level login, not my.myob).",
    "myob.cf_password":
        "Password for that company-file user. Base64(user:pass) is sent as the "
        "x-myobapi-cftoken header - the app does the encoding.",
    "myob.refresh_token":
        "Filled automatically after you complete 'Authorise OAuth' once.",
    # -- QuickBooks Online --
    "qbo.client_id":
        "developer.intuit.com > Dashboard > your app > 'Keys & credentials'. "
        "Use the Production keys once live.",
    "qbo.client_secret":
        "Same Intuit app > Keys & credentials, next to the Client ID.",
    "qbo.redirect_uri":
        "Add it under the Intuit app > Redirect URIs and paste the same value, "
        "e.g. http://localhost:8765/callback",
    "qbo.realm_id":
        "The company id. Shown when you connect the app (OAuth Playground) or "
        "in the URL of your QuickBooks company. Sometimes called 'Company ID'.",
    "qbo.refresh_token":
        "Filled automatically after you complete 'Authorise OAuth' once.",
    # -- Reckon / Sage / FreshBooks --
    "reckon.client_id":
        "developer.reckon.com > register an app for the Reckon One API.",
    "reckon.client_secret": "Issued with the Client ID on the Reckon developer portal.",
    "reckon.redirect_uri": "Match the value set on the Reckon app, e.g. http://localhost:8765/callback",
    "reckon.book_id": "The Reckon One 'Book' id - in the book's URL or via GET /book.",
    "reckon.refresh_token": "Filled automatically after 'Authorise OAuth'.",
    "sage.client_id": "developer.sage.com > Sage Accounting > create an app for OAuth2.",
    "sage.client_secret": "Issued with the Client ID on the Sage developer portal.",
    "sage.redirect_uri": "Match the value set on the Sage app.",
    "sage.refresh_token": "Filled automatically after 'Authorise OAuth'.",
    "freshbooks.client_id": "my.freshbooks.com > Developer > create an app.",
    "freshbooks.client_secret": "Issued with the Client ID in the FreshBooks app settings.",
    "freshbooks.account_id": "Your FreshBooks account id - the code in your dashboard URL.",
    "freshbooks.refresh_token": "Filled automatically after 'Authorise OAuth'.",

    # -- Outlook --
    "outlook.account":
        "The mailbox to watch, e.g. accounts@yourco.com.au. For the COM "
        "backend it must be an account already added to your Outlook desktop "
        "profile.",
    "outlook.folder":
        "Folder display name to scan. 'Inbox' by default; use the exact name "
        "for a sub-folder or rule target.",
    "outlook.graph_client_id":
        "entra.microsoft.com > Entra ID > App registrations > New "
        "registration. Supported account types must be 'Any Entra ID Tenant + "
        "Personal Microsoft accounts'. Copy the 'Application (client) ID' from "
        "the Overview page. No client secret is needed - sign-in uses the "
        "device-code flow, which also needs Authentication > 'Allow public "
        "client flows' = Yes.\n\n"
        "Personal (outlook.com/live.com) account and the portal says "
        "'AADSTS16000 ... does not exist in tenant Microsoft Services'? You "
        "have no Entra directory yet. Creating a tenant directly is now limited "
        "to paying customers, so sign up for the free Azure account at "
        "azure.microsoft.com with this same Microsoft account - that creates a "
        "Default Directory and App registrations then works. Full steps are in "
        "the Setup guide.",
    "outlook.graph_tenant":
        "Leave blank (defaults to 'common', which accepts both personal "
        "outlook.com and work/school accounts). Only set this to your Directory "
        "(tenant) ID if you registered the app as single-tenant.",

    # -- IMAP --
    "imap.host":
        "Your provider's IMAP server. Gmail: imap.gmail.com. Fastmail: "
        "imap.fastmail.com. Yahoo: imap.mail.yahoo.com. iCloud: "
        "imap.mail.me.com. Business/cPanel hosts are usually "
        "mail.yourdomain.com - check your host's 'email client settings' page.",
    "imap.port":
        "993 for IMAP over SSL, which is what almost everyone uses. Only change "
        "it if your provider documents a different port.",
    "imap.username":
        "Usually your full email address. Some business hosts use a separate "
        "mailbox username - check your host's client settings page.",
    "imap.password":
        "An APP PASSWORD, not your normal login password. Gmail: turn on "
        "2-Step Verification, then myaccount.google.com/apppasswords. Yahoo, "
        "iCloud and Fastmail have the same feature under account security. "
        "outlook.com no longer issues working app passwords - use the Graph "
        "backend for those accounts.",
    "imap.folder":
        "INBOX by default. For a sub-folder use the full path as the server "
        "names it, e.g. 'INBOX/Invoices'. If the name is wrong, Test mailbox "
        "lists the folders it can see.",

    # -- AI --
    "ai.model":
        "Model name for the chosen provider. Leave blank to use the default. "
        "OpenAI: gpt-4o-mini. Gemini: gemini-1.5-flash / gemini-2.0-flash. "
        "Anthropic: claude-sonnet-5 (or a Haiku model). For an OpenAI-"
        "compatible host use whatever model id that host exposes.",
    "ai.openai_api_key":
        "platform.openai.com > sign in > Dashboard > API keys > 'Create new "
        "secret key'. Add billing credit under Settings > Billing first.",
    "ai.gemini_api_key":
        "aistudio.google.com > 'Get API key' > Create API key. Free tier is "
        "usually enough for invoice parsing volume.",
    "ai.anthropic_api_key":
        "console.anthropic.com > Settings > API keys > Create Key. Add billing "
        "credit first.",
    "ai.compat_api_key":
        "API key for the OpenAI-compatible host: OpenRouter (openrouter.ai/keys), "
        "Groq (console.groq.com/keys), Together, Azure OpenAI, etc. Leave blank "
        "for a local server (Ollama / LM Studio) that needs no key.",
    "ai.compat_base_url":
        "Base URL of the OpenAI-compatible endpoint, ending in /v1. Examples: "
        "https://openrouter.ai/api/v1 , https://api.groq.com/openai/v1 , "
        "http://localhost:11434/v1 (Ollama), http://localhost:1234/v1 (LM Studio).",

    "watcher.poll_minutes": "How often to check the inbox while the watcher runs.",
}

SETUP_GUIDES: dict[str, str] = {
    "servicem8": (
        "ServiceM8 - Private Application API key\n"
        "1. Sign in to ServiceM8 on the web as an account owner.\n"
        "2. Top-right menu > Add-ons.\n"
        "3. Scroll to 'For Developers' > 'Create a Private Application'.\n"
        "4. Give it a name; tick the scopes you need (at minimum: Job, "
        "Attachment, Client - read/write for attachments).\n"
        "5. Save. Copy the 'API Key' shown.\n"
        "Paste it into the Private App API Key field.\n\n"
        "Job matching: the invoice's job number is matched to a ServiceM8 job "
        "on 'generated_job_id' first, then the internal job number. Make sure "
        "your suppliers quote the ServiceM8 job number on their invoice."
    ),
    "simpro": (
        "simPRO - OAuth2 (client credentials)\n"
        "1. simPRO > System > Setup > Utilities > API Access "
        "(older builds: Setup > Integrations > API).\n"
        "2. Add an OAuth2 client; note the Client ID and Client Secret.\n"
        "3. Build URL is your login URL, e.g. https://acme.simprosuite.com\n"
        "4. Company ID: System > Companies, or GET /api/v1.0/companies/.\n"
        "5. Ensure the client has scope for Jobs and Attachments.\n"
        "Then click 'Authorise OAuth' in Settings."
    ),
    "aroflo": (
        "AroFlo - signed API\n"
        "1. Email AroFlo support / your account manager to enable API access.\n"
        "2. Once enabled: Site Administration > Integrations > AroFlo API.\n"
        "3. Copy API Key, API Secret and the Organisation Encoded value.\n"
        "AroFlo signs each request with an HMAC of these - the app handles it."
    ),
    "tradify": (
        "Tradify - partner OAuth2\n"
        "Tradify does not offer self-serve API keys. Apply at "
        "tradify.com/integrations or email api@tradify.com describing the "
        "integration. They issue a Client ID + Secret and whitelist your "
        "redirect URI. Then use 'Authorise OAuth'."
    ),
    "fergus": (
        "Fergus - Personal Access Token\n"
        "1. If you don't see an API menu, ask Fergus support to turn on API "
        "access for your account.\n"
        "2. Avatar > Settings > Fergus API (or Developer).\n"
        "3. Generate a Personal Access Token and copy it.\n"
    ),
    "jobber": (
        "Jobber - OAuth2\n"
        "1. developer.getjobber.com > sign in with your Jobber login.\n"
        "2. Apps > New App. Set the Redirect URI (e.g. "
        "http://localhost:8765/callback) and request the Jobs + Notes/"
        "Attachments scopes.\n"
        "3. Copy Client ID + Client Secret.\n"
        "4. Put the same redirect URI here, then 'Authorise OAuth'."
    ),
    "servicetitan": (
        "ServiceTitan - OAuth2 + App Key\n"
        "1. developer.servicetitan.io > Applications > create an application.\n"
        "2. In ServiceTitan: Settings > Integrations > API Application Access - "
        "an admin approves your app for the tenant and reveals the ST-App-Key.\n"
        "3. Copy Client ID, Client Secret, App Key, and your Tenant ID.\n"
    ),
    "housecallpro": (
        "Housecall Pro - API key\n"
        "API access is on the Max plan. Settings > API & Integrations to "
        "generate a key, or contact Housecall Pro support / their developer "
        "portal for one."
    ),
    "xero": (
        "Xero - OAuth2\n"
        "1. developer.xero.com > My Apps > New app.\n"
        "2. App type 'Web app'. Company URL and a Redirect URI you control "
        "(e.g. http://localhost:8765/callback).\n"
        "3. Open the app > Configuration: copy Client id, 'Generate a secret'.\n"
        "4. Paste Client ID, Secret and the same Redirect URI here.\n"
        "5. 'Authorise OAuth', sign in, pick the organisation.\n"
        "6. Tenant ID: call GET https://api.xero.com/connections (or re-run "
        "'Test accounting' and read it from the log) and paste it in.\n"
        "Scopes needed: accounting.transactions, accounting.attachments, "
        "accounting.contacts, offline_access."
    ),
    "myob": (
        "MYOB (AccountRight / Business) - OAuth2 + company file\n"
        "1. developer.myob.com > sign in > Register a new app ('Desktop').\n"
        "2. Set the Redirect URL (e.g. http://localhost:8765/callback).\n"
        "3. Copy 'API Key' (= Client ID) and the Client Secret.\n"
        "4. 'Authorise OAuth' here, sign in with my.myob.\n"
        "5. Company File ID: call GET https://api.myob.com/accountright/ - copy "
        "the file's Id (GUID).\n"
        "6. Company File Username/Password: the login for that specific file "
        "(set under Setup > User Access in the file). If the file has no "
        "password, use the file 'Administrator' with a blank password."
    ),
    "qbo": (
        "QuickBooks Online - OAuth2\n"
        "1. developer.intuit.com > Dashboard > Create an app > QuickBooks "
        "Online Accounting.\n"
        "2. Keys & credentials: copy Client ID + Client Secret (Development "
        "keys first, Production once approved).\n"
        "3. Add your Redirect URI (e.g. http://localhost:8765/callback).\n"
        "4. 'Authorise OAuth' here and connect a company.\n"
        "5. Realm ID (Company ID) is shown on connect and in the OAuth "
        "playground; paste it in."
    ),
    "reckon": (
        "Reckon One - OAuth2\n"
        "developer.reckon.com > register an app for the Reckon One API. Copy "
        "Client ID/Secret, set the redirect URI, then 'Authorise OAuth'. Book "
        "ID is in your Reckon One book URL."
    ),
    "sage": (
        "Sage Accounting - OAuth2\n"
        "developer.sage.com > Sage Accounting > create an app. Copy Client "
        "ID/Secret, set the callback URL, then 'Authorise OAuth'."
    ),
    "freshbooks": (
        "FreshBooks - OAuth2\n"
        "my.freshbooks.com > Developer > create an app. Copy Client ID/Secret, "
        "set the redirect URI, then 'Authorise OAuth'. Account ID is the code "
        "in your FreshBooks dashboard URL."
    ),
    "outlook_com": (
        "Outlook - COM backend (CLASSIC desktop Outlook only)\n"
        "No credentials. The app automates the classic Outlook desktop client "
        "already signed in on this PC.\n"
        "- Enter the mailbox address in 'Mailbox / account to monitor' exactly "
        "as it appears in Outlook (or leave blank for the default account). If "
        "it doesn't match, Test Outlook lists the accounts it can see.\n"
        "- Outlook must be running (or allowed to start).\n"
        "- 'Folder name' defaults to Inbox; set a sub-folder name if a rule "
        "sorts invoices there.\n\n"
        "IMPORTANT - when COM will NOT work:\n"
        "- The NEW Outlook for Windows (the Store app) has no COM automation "
        "interface at all.\n"
        "- Classic Outlook requires a paid Microsoft 365 subscription.\n"
        "- If Test Outlook reports only an 'Outlook Data File' with 0 items, "
        "your mail is not in a classic profile.\n"
        "In any of those cases use the 'graph' backend instead."
    ),
    "outlook_graph": (
        "Email - Microsoft Graph backend (new Outlook, outlook.com, or no "
        "desktop Outlook at all)\n"
        "Use this when COM cannot work. Microsoft disabled app-password / IMAP "
        "(Basic auth) for personal Outlook accounts on 16 Sept 2024, so OAuth2 "
        "is the only supported route - but sign-in here needs only a Client "
        "ID.\n\n"
        "STEP 1 - make sure you have a directory\n"
        "Go to entra.microsoft.com and sign in with the SAME Microsoft account "
        "whose mail you want to read.\n"
        "  - If you land on a dashboard and can see 'App registrations', you "
        "already have a Default Directory: skip to step 2.\n"
        "  - If you get 'Interaction required' / AADSTS16000 saying your "
        "live.com account 'does not exist in tenant Microsoft Services', you "
        "have no directory yet. Microsoft now lets only PAYING customers "
        "create a tenant directly, so sign up for the free Azure account at "
        "azure.microsoft.com with this same Microsoft account - that creates a "
        "'Default Directory' for you. A card is required for identity "
        "verification; the free tier is not charged, and app registration "
        "stays on the always-free Entra tier afterwards. Then return to "
        "entra.microsoft.com.\n"
        "  - Would rather not? Use the IMAP backend instead - but IMAP does "
        "NOT work with outlook.com, so you would auto-forward the invoices to "
        "e.g. a Gmail address first.\n\n"
        "STEP 2 - register the app\n"
        "1. entra.microsoft.com > Entra ID > App registrations > New "
        "registration.\n"
        "2. Name: InvoiceM8\n"
        "3. Supported account types: 'Any Entra ID Tenant + Personal Microsoft "
        "accounts'. This one matters - a personal outlook.com mailbox cannot "
        "sign in without it.\n"
        "4. Redirect URI: leave blank. Select Register.\n"
        "5. On the Overview page copy the 'Application (client) ID' and paste "
        "it into the Application (client) ID field in InvoiceM8. Leave Tenant "
        "blank.\n\n"
        "STEP 3 - allow device-code sign-in\n"
        "In the app: Manage > Authentication > scroll to 'Advanced settings' > "
        "set 'Allow public client flows' to YES > Save. Sign-in fails without "
        "this.\n\n"
        "STEP 4 - permission to read mail\n"
        "In the app: Manage > API permissions > Add a permission > Microsoft "
        "Graph > Delegated permissions > tick Mail.Read > Add permissions. A "
        "personal account consents at sign-in, so no admin consent is needed.\n\n"
        "STEP 5 - sign in\n"
        "Back in InvoiceM8: Save settings, then click 'Sign in to Microsoft'. "
        "A short code appears and your browser opens "
        "microsoft.com/devicelogin - enter the code and sign in. Then click "
        "Test mailbox.\n\n"
        "Notes:\n"
        "- Leave 'Mailbox / account to monitor' BLANK. Graph reads whichever "
        "mailbox you signed in as, so this picks the right account "
        "automatically. Only set it to another address if you have an "
        "organisation tenant with admin-consented access to that mailbox.\n"
        "- The sign-in is stored encrypted on this PC and refreshes itself; "
        "you sign in once."
    ),
    "outlook_imap": (
        "Email - IMAP backend (Gmail, Fastmail, Yahoo, iCloud, business hosts)\n"
        "The simplest option when it is available: no Azure, no app "
        "registration, no subscription. You need the server name and an APP "
        "PASSWORD.\n\n"
        "Gmail (most common):\n"
        "1. myaccount.google.com > Security > turn ON 2-Step Verification "
        "(app passwords are unavailable without it).\n"
        "2. Go to myaccount.google.com/apppasswords\n"
        "3. Name it 'InvoiceM8' and Create. Copy the 16-character password.\n"
        "4. In InvoiceM8: IMAP server imap.gmail.com, Port 993, Username your "
        "full Gmail address, App password the 16 characters (spaces are fine), "
        "Folder INBOX.\n"
        "5. Save settings, then Test mailbox.\n\n"
        "Other providers - same idea, different server:\n"
        "  Fastmail  imap.fastmail.com    993\n"
        "  Yahoo     imap.mail.yahoo.com  993\n"
        "  iCloud    imap.mail.me.com     993\n"
        "  Zoho      imap.zoho.com        993\n"
        "  Business/cPanel: usually mail.yourdomain.com - see your host's "
        "'email client settings' page.\n\n"
        "IMPORTANT - outlook.com / hotmail.com / live.com:\n"
        "Microsoft turned off app-password (Basic auth) access for personal "
        "Microsoft accounts on 16 September 2024, so IMAP cannot work with "
        "them at all. Either use the 'graph' backend, or add a rule in "
        "Outlook.com that auto-forwards invoice emails to a Gmail address and "
        "point IMAP at that instead.\n\n"
        "Notes:\n"
        "- Mail is read with BODY.PEEK, so InvoiceM8 never marks your messages "
        "as read.\n"
        "- Only emails WITH attachments are queued; plain emails are ignored."
    ),
    "gemini": (
        "Google Gemini API key\n"
        "1. aistudio.google.com > sign in.\n"
        "2. 'Get API key' (left nav) > Create API key > pick / create a "
        "Google Cloud project.\n"
        "3. Copy the key. Model: gemini-1.5-flash or gemini-2.0-flash.\n"
        "The free tier limit is usually well above invoice-parsing volume."
    ),
    "anthropic": (
        "Anthropic (Claude) API key\n"
        "1. console.anthropic.com > sign in.\n"
        "2. Add a payment method / credit under Billing.\n"
        "3. Settings > API keys > Create Key. Copy it now (shown once).\n"
        "Model: claude-sonnet-5 (or a Haiku model for lower cost)."
    ),
}
