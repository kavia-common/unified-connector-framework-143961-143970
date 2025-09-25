# unified-connector-framework-143961-143970

Backend (FastAPI) is scaffolded under unified_connector_backend with:
- Connector core (BaseConnector, registry, manager)
- MongoDB persistence (connections, tokens, sync_states, audit_logs)
- Encryption service (Fernet)
- API routes: / (health), /api/connectors, /api/connections
- Logging and config with Ocean Professional theme metadata

Key endpoints (enveloped):
- GET   /api/connectors
- GET   /api/connectors/{id}
- PATCH /api/connectors/{id}
- POST  /api/connectors/{id}/probe
- POST  /api/connectors/{id}/jobs
- POST  /api/connectors/{id}/connect                # oauth2/api_key init
- POST  /api/connectors/{id}/connect/callback       # completion (code or api key)
- POST  /api/connectors/{id}/validate
- POST  /api/connectors/{id}/revoke
- GET   /api/connectors/{id}/containers
- GET   /api/connectors/{id}/items
- GET   /api/connectors/{id}/comments
- POST  /api/connectors/{id}/webhooks
- DELETE /api/connectors/{id}/webhooks

- GET   /api/connections                            # (scaffold list)
- POST  /api/connections                            # upsert (create or update)
- POST  /api/connections/token                      # persist encrypted token
- POST  /api/connections/validate                   # connector.validate
- POST  /api/connections/revoke                     # revoke (stub)
- GET   /api/connections/{connectionId}/token       # fetch plaintext (internal use)
- GET   /api/connections/{connectionId}/sync-state  # get cursor
- POST  /api/connections/{connectionId}/sync-state  # set cursor

OAuth/PKCE and CSRF:
- CSRF state and PKCE helpers scaffolded in src/core/oauth.py.
- For production, store PKCE code_verifier server-side and validate state against cookie (double submit).
- Current implementation returns codeVerifier to client for development.

Getting started:
1) cd unified_connector_backend
2) cp .env.example .env  # fill ENCRYPTION_KEY and Mongo settings
3) pip install -r requirements.txt
4) uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

Generate OpenAPI file for interfaces/:
python -m src.api.generate_openapi

Key environment variables:
- MONGODB_URL, MONGODB_DB
- ENCRYPTION_KEY (Fernet key)
- LOG_LEVEL, LOG_JSON
- API_PREFIX

OpenAPI docs at /docs when running.

Note: Example connectors (PostgreSQL, Salesforce) are stubs for development.
New: Production-grade example connectors added:
- Jira (OAuth2 or API key) under src/connectors/jira
- Confluence (OAuth2 or API key) under src/connectors/confluence

Usage:
- List connectors: GET /api/connectors
- Probe Jira: POST /api/connectors/jira/probe (via jobs or probe endpoint) or /api/connectors/jira/validate
- Containers/items/comments via:
  - GET /api/connectors/{id}/containers
  - GET /api/connectors/{id}/items
  - GET /api/connectors/{id}/comments

Config examples (request bodies):
{
  "base_url": "https://your-domain.atlassian.net",
  "auth_method": "api_key",
  "api_email": "you@example.com",
  "api_token": "<jira_api_token>"
}
or OAuth2:
{
  "base_url": "https://your-domain.atlassian.net",
  "auth_method": "oauth2",
  "access_token": "<access>",
  "refresh_token": "<refresh>",
  "client_id": "<client_id>",
  "client_secret": "<client_secret>",
  "scopes": ["read:jira-work", "offline_access"]
}

Security: Do not hardcode secrets; use /api/connections/token for encrypted storage.
