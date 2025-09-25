"""
Connectors package initializer ensures example and Atlassian connectors are registered on import.
"""

# Register example connectors for scaffolding
from . import examples  # noqa: F401

# Register Atlassian connectors (Jira, Confluence)
from .jira.connector import JiraConnector  # noqa: F401
from .confluence.connector import ConfluenceConnector  # noqa: F401
from .registry import registry as _registry  # noqa: F401

# Instantiate and register on import to make them available in /api/connectors
_registry.register(JiraConnector())
_registry.register(ConfluenceConnector())
