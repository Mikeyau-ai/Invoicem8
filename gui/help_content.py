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
    "outlook.graph_tenant_id":
        "Azure Portal > Microsoft Entra ID > Overview > 'Directory (tenant) ID'.",
    "outlook.graph_client_id":
        "Azure Portal > Entra ID > App registrations > your app > 'Application "
        "(client) ID'.",
    "outlook.graph_client_secret":
        "Same app > Certificates & secrets > New client secret. Copy the "
        "Value (not the Secret ID) right away.",
    "outlook.graph_refresh_token":
        "From the OAuth consent flow. The app > API permissions must include "
        "Mail.Read with admin consent granted.",

    # -- AI --
    "ai.model":
        "Model name for the chosen provider. Gemini: gemini-1.5-flash or "
        "gemini-2.0-flash. Anthropic: claude-sonnet-5. Flash/Haiku-class "
        "models are cheapest and fine for this.",
    "ai.gemini_api_key":
        "aistudio.google.com > 'Get API key' > Create API key. Free tier is "
        "usually enough for invoice parsing volume.",
    "ai.anthropic_api_key":
        "console.anthropic.com > Settings > API keys > Create Key. Add billing "
        "credit first.",

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
        "Outlook - COM backend (recommended for a single PC)\n"
        "No credentials. The app talks to the Outlook desktop client that is "
        "already open and signed in on this machine.\n"
        "- Enter the mailbox address in 'Mailbox / account to monitor' exactly "
        "as it appears in Outlook (or leave blank for the default account).\n"
        "- Outlook must be running (or allowed to start) for the watcher to "
        "read mail.\n"
        "- 'Folder name' defaults to Inbox; set a sub-folder name if you sort "
        "invoices with a rule."
    ),
    "outlook_graph": (
        "Outlook - Microsoft Graph backend (no desktop Outlook needed)\n"
        "1. Azure Portal > Microsoft Entra ID > App registrations > New "
        "registration. Single tenant is fine.\n"
        "2. Overview: copy 'Directory (tenant) ID' and 'Application (client) "
        "ID'.\n"
        "3. Certificates & secrets > New client secret - copy the Value.\n"
        "4. API permissions > Add > Microsoft Graph > Mail.Read "
        "(Delegated for a user mailbox, Application for app-only) > 'Grant "
        "admin consent'.\n"
        "5. Authentication > add a redirect URI if using delegated flow.\n"
        "6. Paste tenant/client/secret here; the refresh token is filled by "
        "the consent flow.\n"
        "'Mailbox / account to monitor' = the UPN of the mailbox to read."
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
