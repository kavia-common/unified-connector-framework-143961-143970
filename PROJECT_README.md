# Unified Connector Framework — Project Guide

This document summarizes environment setup, architecture, OAuth onboarding, unified envelope, and API usage for both backend and frontend.

Components:
- Backend (FastAPI): unified_connector_backend
- Frontend (Next.js, planned): unified_connector_frontend
- Database: MongoDB (used by backend)

Setup (Backend):
1) cd unified_connector_backend
2) cp .env.example .env
3) python -m pip install -r requirements.txt
4) uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
Docs: http://localhost:8000/docs

Setup (Frontend, planned):
1) cd unified_connector_frontend
2) cp .env.example .env.local
3) npm i && npm run dev
App: http://localhost:3000

Environment variables:
- Backend: see unified_connector_backend/.env.example
- Frontend: see unified_connector_frontend/.env.example
Note: Do not commit secrets. Request appropriate values from your environment owner.

Unified Envelope:
- All REST responses are wrapped:
  Success: { "ok": true, "data": {...} }
  Error: HTTP 4xx/5xx with detail: { "code": "invalid_request"|"not_found"|..., "message": "...", "details": {...}? }

Headers:
- X-Tenant-Id: required for tenant/workspace scoping
- X-Request-Id or X-Correlation-Id: optional; backend will generate one if absent

OAuth/PKCE flow (summary):
1) Init:
   POST /api/connectors/{id}/connect
   Body: { "workspaceId": "...", "method": "oauth2", "redirectUri": "https://app.example.com/oauth/callback", "scopes": ["..."] }
   Response: { "authUrl", "state", "codeChallenge", "codeVerifier" }
   Note: In production, store codeVerifier on the server and validate CSRF via double-submit cookie.
2) Redirect user to authUrl, then handle /oauth/callback with ?code&state.
3) Complete:
   POST /api/connectors/{id}/connect/callback
   Body: { "workspaceId": "...", "code": "...", "state": "...", "codeVerifier": "..." }
   Response: { "connectionId", "status": "connected" }
4) Persist tokens:
   POST /api/connections/token
   Body: { "connectionId": "...", "token": "..." } (encrypted at rest)

API quick examples (curl):

- List connectors:
  curl -H "X-Tenant-Id: t_123" http://localhost:8000/api/connectors

- Validate connector configuration:
  curl -X POST -H "Content-Type: application/json" -H "X-Tenant-Id: t_123" \
    -d '{"workspaceId":"t_123","config":{"base_url":"https://your-domain.atlassian.net","auth_method":"oauth2"}}' \
    http://localhost:8000/api/connectors/jira/validate

- Probe:
  curl -X POST -H "Content-Type: application/json" -H "X-Tenant-Id: t_123" \
    -d '{"base_url":"https://your-domain.atlassian.net","auth_method":"oauth2","scopes":["read:jira-work"]}' \
    http://localhost:8000/api/connectors/jira/probe

- Start OAuth:
  curl -X POST -H "Content-Type: application/json" -H "X-Tenant-Id: t_123" \
    -d '{"workspaceId":"t_123","method":"oauth2","redirectUri":"http://localhost:3000/oauth/callback","scopes":["read:jira-work","offline_access"]}' \
    http://localhost:8000/api/connectors/jira/connect

- Complete OAuth (after redirect):
  curl -X POST -H "Content-Type: application/json" -H "X-Tenant-Id: t_123" \
    -d '{"workspaceId":"t_123","code":"<code>","state":"<state>","codeVerifier":"<verifier>"}' \
    http://localhost:8000/api/connectors/jira/connect/callback

- Persist token (api_key path or token exchange result):
  curl -X POST -H "Content-Type: application/json" -H "X-Tenant-Id: t_123" \
    -d '{"connectionId":"jira:t_123:oauth","token":"<access_or_api_token>"}' \
    http://localhost:8000/api/connections/token

Unified resource browsing:
- Containers: GET /api/connectors/{id}/containers?workspaceId=...&cursor=&limit=
- Items:      GET /api/connectors/{id}/items?workspaceId=...&containerId=&cursor=&limit=
- Comments:   GET /api/connectors/{id}/comments?workspaceId=...&itemId=...&cursor=&limit=

Security notes:
- Set ENCRYPTION_KEY in production; otherwise secrets are encrypted with a process-local ephemeral key and will not survive restarts.
- Secrets are masked in logs; avoid logging request bodies that contain credentials.
- Store tokens via the /api/connections/token endpoint; never return secrets to the browser unless strictly necessary.

Architecture:
- Connectors implement validate, probe, execute, and optional resource methods (containers/items/comments/create).
- Registry makes connectors discoverable; Manager orchestrates calls and validation.
- MongoDB stores connections, tokens, cursors, and audit logs.
- Middleware attaches tenant/correlation context and emits structured logs.

See also:
- Backend README: unified_connector_backend/README.md
- Assets (design + flows): assets/
