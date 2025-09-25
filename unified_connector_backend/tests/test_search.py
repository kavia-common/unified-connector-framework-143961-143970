"""
Smoke tests for unified resource browsing/search style endpoints.

Covers:
- GET /api/connectors -> list
- GET /api/connectors/{id} -> detail
- GET /api/connectors/{id}/containers
- GET /api/connectors/{id}/items
- GET /api/connectors/{id}/comments
- Error for unknown connector on GET detail and probe/job validate
"""

from fastapi.testclient import TestClient
import pytest

from src.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def _assert_envelope_ok(resp):
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    return data["data"]


def test_list_connectors_and_get_details(client):
    data = _assert_envelope_ok(client.get("/api/connectors"))
    assert isinstance(data, list)
    ids = [c["id"] for c in data]
    assert "jira" in ids
    assert "confluence" in ids

    # get details for jira
    detail = _assert_envelope_ok(client.get("/api/connectors/jira"))
    assert detail["id"] == "jira"
    assert isinstance(detail["config"], dict)


def test_containers_items_comments_smoke(client):
    # Containers
    containers = _assert_envelope_ok(client.get("/api/connectors/jira/containers", params={"workspaceId": "t1"}))
    assert "items" in containers and isinstance(containers["items"], list)

    # Items
    items = _assert_envelope_ok(
        client.get("/api/connectors/jira/items", params={"workspaceId": "t1", "containerId": "PRJ"})
    )
    assert "items" in items and isinstance(items["items"], list)

    # Comments
    comments = _assert_envelope_ok(
        client.get("/api/connectors/jira/comments", params={"workspaceId": "t1", "itemId": "PRJ-1"})
    )
    assert "items" in comments and isinstance(comments["items"], list)


def test_unknown_connector_404(client):
    r = client.get("/api/connectors/unknown-one")
    assert r.status_code == 404

    # probe or job on unknown id should error via connectors endpoints
    r2 = client.post("/api/connectors/unknown-one/probe", json={})
    assert r2.status_code in (400, 404)  # unified error mapping returns 400 or 404 depending on path
