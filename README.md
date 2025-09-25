# Unified Connector Framework

A fullstack framework for integrating multiple external APIs through a unified interface and envelope format. It provides:
- Backend (FastAPI) at unified_connector_backend: modular connectors (BaseConnector, registry, manager), OAuth helpers, unified response envelope, MongoDB persistence (connections, tokens, sync states, audit logs), encryption service, and structured logging with tenant scoping.
- Frontend (Next.js + Tailwind) planned at unified_connector_frontend: connection onboarding wizard, management dashboard, unified resource browsing (not included in this workspace snapshot).

Key patterns:
- Unified Envelope: All API responses follow { ok, data, error }.
- Tenant Scoping: Each API call should include X-Tenant-Id; correlation IDs are supported via X-Request-Id.
- OAuth + API Key: Connectors support oauth2 and api_key flows consistently.

Repository structure:
- unified_connector_backend/  FastAPI backend (this workspace)
- assets/                    Design and architecture notes
- attachments/               Reference docs and visuals

Quick start (Backend):
1) cd unified_connector_backend
2) cp .env.example .env  # fill ENCRYPTION_KEY and Mongo settings
3) python -m pip install -r requirements.txt
4) uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
OpenAPI docs: http://localhost:8000/docs
Generate static OpenAPI: python -m src.api.generate_openapi (writes interfaces/openapi.json)

Backend features (highlights):
- API routes: / (health), /api/connectors, /api/connections
- Connector implementations: Jira and Confluence (production-grade examples), PostgreSQL and Salesforce (stubs)
- Encryption (Fernet) for secrets; masked logs
- MongoDB persistence via Motor; token store and cursors
- Middleware for tenant/correlation/metrics and JSON logs
- OAuth helpers: CSRF state + PKCE S256

Environment variables (see .env.example in backend for details):
- MONGODB_URL, MONGODB_DB
- ENCRYPTION_KEY (Fernet key; required for production)
- LOG_LEVEL, LOG_JSON
- API_PREFIX

Unified envelope:
- Success: { "ok": true, "data": { ... } }
- Error: HTTPException with detail in UnifiedError: { code, message, details? }
All routes in /api return Envelope responses.

Headers required:
- X-Tenant-Id: tenant/workspace scoping (required by convention)
- X-Request-Id or X-Correlation-Id: optional; server generates one if absent

OAuth summaries:
- Init: POST /api/connectors/{id}/connect { method: "oauth2", redirectUri, scopes[] } → { authUrl, state, codeChallenge, codeVerifier }
- Callback: POST /api/connectors/{id}/connect/callback { code/state/codeVerifier } → { connectionId, status }
- API key: init returns expected header hint; complete via callback with apiKey/apiSecret

Unified resource search (scaffold):
- Containers/items/comments endpoints exposed per connector to browse resources consistently.

Frontend (placeholder):
- Next.js + Tailwind app expected under unified_connector_frontend with env variables for backend base URL and SITE_URL for OAuth redirects. See section below for .env.example template.

License: Proprietary (example).

For more, see:
- unified_connector_backend/README.md for backend details
- assets/ for design notes on dashboard, flows, and style guide