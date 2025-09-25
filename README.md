# unified-connector-framework-143961-143970

Backend (FastAPI) is scaffolded under unified_connector_backend with:
- Connector core (BaseConnector, registry, manager)
- MongoDB persistence (connections, tokens, sync_states, audit_logs)
- Encryption service (Fernet)
- API routes: / (health), /api/connectors, /api/connections
- Logging and config with Ocean Professional theme metadata

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