# Unified Connector Backend (FastAPI)

This service exposes REST APIs to manage connectors, drive OAuth/API Key onboarding, persist connection credentials, and browse resources using a unified response envelope.

Core capabilities:
- Modular connector architecture: BaseConnector, registry, manager
- Production-grade example connectors: Jira and Confluence; example stubs: PostgreSQL, Salesforce
- Unified Envelope responses: { ok, data, error }
- OAuth/PKCE helpers and consistent connect/connect/callback routes
- MongoDB persistence (connections, tokens, sync_states, audit_logs)
- Token encryption via Fernet with masked logs and tenant-aware context
- Structured JSON logging with correlation and tenant scoping

Quick start:
1) cp .env.example .env
2) python -m pip install -r requirements.txt
3) uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
Docs: http://localhost:8000/docs
Generate static OpenAPI: python -m src.api.generate_openapi (writes interfaces/openapi.json)

Environment variables (.env.example included):
- APP_NAME, APP_DESCRIPTION, APP_VERSION
- API_PREFIX=/api
- MONGODB_URL, MONGODB_DB
- ENCRYPTION_KEY  # base64-urlsafe 32-byte key; REQUIRED for production
- LOG_LEVEL=INFO, LOG_JSON=false
- CORS_ALLOW_ORIGINS=["*"], CORS_ALLOW_HEADERS=["*"], etc.

Unified Envelope format:
- Success: { "ok": true, "data": { ... } }
- Error: HTTP 4xx/5xx with detail UnifiedError { code, message, details? }

Headers:
- X-Tenant-Id: tenant/workspace scoping (recommended/expected)
- X-Request-Id or X-Correlation-Id: optional; auto-generated if absent
- X-Api-Tag: optional; included in completion logs

Key endpoints:
- Health: GET /
- Connectors:
  - GET /api/connectors
  - GET /api/connectors/{id}
  - PATCH /api/connectors/{id}
  - POST /api/connectors/{id}/probe
  - POST /api/connectors/{id}/jobs
  - POST /api/connectors/{id}/connect
  - POST /api/connectors/{id}/connect/callback
  - POST /api/connectors/{id}/validate
  - POST /api/connectors/{id}/revoke
  - GET  /api/connectors/{id}/containers
  - GET  /api/connectors/{id}/items
  - GET  /api/connectors/{id}/comments
  - POST /api/connectors/{id}/webhooks
  - DELETE /api/connectors/{id}/webhooks
- Connections:
  - GET  /api/connections
  - POST /api/connections
  - POST /api/connections/token
  - POST /api/connections/validate
  - POST /api/connections/revoke
  - GET  /api/connections/{connectionId}/token
  - GET  /api/connections/{connectionId}/sync-state
  - POST /api/connections/{connectionId}/sync-state

OAuth & API Key flows (summary):
- OAuth Init:
  POST /api/connectors/{id}/connect
  Body: { workspaceId, method: "oauth2", redirectUri, scopes[], csrfToken? }
  Returns: { authUrl, state, codeChallenge, codeVerifier }
  Note: In production, store codeVerifier server-side and validate CSRF (double submit cookie).
- OAuth Callback:
  POST /api/connectors/{id}/connect/callback
  Body: { workspaceId, code, state, codeVerifier }
  Returns: { connectionId, status: "connected" }
- API Key:
  Init returns expected header hint; complete with:
  POST /api/connectors/{id}/connect/callback
  Body: { workspaceId, apiKey, apiSecret? }
  Returns: { connectionId, status: "connected" }
- Persist encrypted tokens:
  POST /api/connections/token
  Body: { connectionId, token } → stored encrypted via Fernet
- Validate configuration:
  POST /api/connectors/{id}/validate or /api/connections/validate

Unified resource browsing:
- Containers/items/comments exposed at connectors endpoints to standardize resource exploration across providers.

Security:
- Never log secrets; middleware masks common sensitive keys.
- Require ENCRYPTION_KEY in production; without it, a per-process ephemeral key is generated (non-persistent).
- Use /api/connections/token to store secrets; avoid returning secrets to clients.

Architecture overview:
- src/connectors/*: base, registry, manager, and per-provider adapters (jira, confluence)
- src/core/*: config, logging, middleware, oauth, security, errors
- src/models/*: Pydantic schemas and envelope
- src/db/*: Mongo client setup
- src/services/encryption.py: Fernet-based encryption
- src/api/routes/*: FastAPI routers for health, connectors, connections

Testing (minimal guidance):
- Unit: registry behavior, mapping helpers
- Integration (scaffold): OAuth init/callback flow returns expected envelope and structure
- Smoke: containers/items/comments routes return enveloped, non-error responses for stub configs

Notes:
- Jira/Confluence examples are designed to be production-grade but should not be used without configuring real credentials.
- Example DB/SaaS connectors are stubs for development and testing.

License: Proprietary (example).
