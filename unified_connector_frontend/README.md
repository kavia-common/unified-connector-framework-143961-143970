# Unified Connector Frontend (Next.js + Tailwind)

This is a placeholder README for the frontend application that will deliver:
- Connection onboarding wizard (OAuth/API Key)
- Management dashboard (Connectors grouped by DB/SaaS)
- Unified resource browsing (containers/items/comments)

Framework:
- Next.js (App Router)
- Tailwind CSS
- React Query/SWR for data fetching (recommended)

Environment variables (.env.example provided):
- NEXT_PUBLIC_API_BASE_URL: Base URL of the backend (e.g., http://localhost:8000)
- NEXT_PUBLIC_SITE_URL: Public URL of the frontend (used for OAuth redirect targets)
- NEXT_PUBLIC_APP_NAME: Display name

Setup (planned):
1) cp .env.example .env.local
2) pnpm install (or npm/yarn)
3) pnpm dev
4) Access app at http://localhost:3000

OAuth integration notes:
- During connect init, call POST {API_BASE}/api/connectors/{id}/connect with method="oauth2", redirectUri = `${NEXT_PUBLIC_SITE_URL}/oauth/callback`, and scopes.
- On callback route (/oauth/callback), parse code/state and POST to {API_BASE}/api/connectors/{id}/connect/callback with the code, state, and previously held codeVerifier.
- For API key onboarding, use connect init for hints, then complete via /connect/callback with apiKey/apiSecret.

Unified envelope handling in UI:
- All responses shape: { ok: boolean, data?: any, error?: string }
- Handle errors by reading http status and detail; show user-friendly messages.

Headers to include in all API calls:
- X-Tenant-Id: current workspace id from user/session
- Optional: X-Request-Id for correlation

Design guidelines:
- Follow assets/style_guide.md and connections_dashboard_design_notes.md
- Theme: Ocean Professional (blue primary, amber accents), subtle shadows, rounded corners

This document guides integration until the frontend code is scaffolded in this repository.
