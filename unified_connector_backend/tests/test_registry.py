"""
Tests for the in-memory connector registry.

Covers:
- registering connectors
- listing all
- fetching by id
- correctness of registered default connectors
"""

from src.connectors.registry import ConnectorRegistry, registry
from src.connectors.base import BaseConnector


class DummyConnector(BaseConnector):
    def __init__(self) -> None:
        super().__init__("dummy", "saas", "Dummy")

    async def validate(self, config):
        return None

    async def probe(self, config):
        return {"ok": True}

    async def execute(self, job_type, config, params):
        return "job-1"


def test_registry_add_and_fetch():
    reg = ConnectorRegistry()
    c = DummyConnector()
    reg.register(c)

    # fetch returns same instance
    got = reg.get("dummy")
    assert got is c
    assert list(reg.all()) == [c]


def test_registry_overwrite_same_id():
    reg = ConnectorRegistry()
    c1 = DummyConnector()
    c2 = DummyConnector()
    reg.register(c1)
    reg.register(c2)  # same id; should overwrite

    assert reg.get("dummy") is c2
    assert len(list(reg.all())) == 1


def test_global_registry_contains_expected_connectors():
    """
    The repo registers Jira, Confluence, Salesforce, and Postgres at import time.
    We verify at least jira and confluence exist and have expected attributes.
    """
    ids = {c.connector_id for c in registry.all()}
    # Basic presence check; examples also register salesforce and postgres
    assert "jira" in ids
    assert "confluence" in ids
    # Optional extra
    assert "salesforce" in ids
    assert "postgres" in ids

    jira = registry.get("jira")
    assert jira is not None
    assert hasattr(jira, "connector_id") and jira.connector_id == "jira"
    assert hasattr(jira, "group") and jira.group in ("db", "saas")
    assert isinstance(jira.example_fields(), dict)
