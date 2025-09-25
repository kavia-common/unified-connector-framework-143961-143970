"""
Integration-like tests for OAuth flow endpoints using TestClient.

Covers:
- OAuth init: POST /api/connectors/{id}/connect with method="oauth2"
- OAuth callback: POST /api/connectors/{id}/connect/callback with code/state
- Persist token: POST /api/connections/token (monkeypatched DB layer)
"""

from fastapi.testclient import TestClient
import pytest

from src.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_oauth_init_returns_auth_data(client):
    resp = client.post(
        "/api/connectors/jira/connect",
        json={
            "workspaceId": "t_123",
            "method": "oauth2",
            "redirectUri": "http://localhost:3000/oauth/callback",
            "scopes": ["read:jira-work", "offline_access"],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    data = body["data"]
    assert "authUrl" in data and data["authUrl"].startswith("https://auth.example.com/authorize")
    assert "state" in data and data["state"]
    assert "codeChallenge" in data and data["codeChallenge"]
    assert "codeVerifier" in data and data["codeVerifier"]


def test_oauth_callback_returns_connection_id(client):
    # Simulate callback completion
    resp = client.post(
        "/api/connectors/jira/connect/callback",
        json={"workspaceId": "t_123", "code": "abc123", "state": "state1", "codeVerifier": "ver1"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["data"]["status"] == "connected"
    assert body["data"]["connectionId"].startswith("jira:t_123:")


def test_persist_token_monkeypatched(client, monkeypatch):
    # Monkeypatch store_token to avoid Mongo
    called = {}

    async def fake_store_token(connection_id, token, expires_at):
        called["args"] = (connection_id, token, expires_at)
        return "tok_1"

    monkeypatch.setattr("src.models.collections.store_token", fake_store_token)

    resp = client.post(
        "/api/connections/token",
        json={"connectionId": "jira:t_123:oauth", "token": "secret-token"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["data"]["tokenId"] == "tok_1"
    assert called["args"][0] == "jira:t_123:oauth"
    assert called["args"][1] == "secret-token"
