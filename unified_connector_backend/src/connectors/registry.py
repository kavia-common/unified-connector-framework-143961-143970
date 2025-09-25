"""
Simple in-memory connector registry.
"""

from typing import Dict, Iterable, Optional

from .base import BaseConnector


class ConnectorRegistry:
    """Registry for all available connector implementations."""

    def __init__(self) -> None:
        self._items: Dict[str, BaseConnector] = {}

    # PUBLIC_INTERFACE
    def register(self, connector: BaseConnector) -> None:
        """Register a connector instance."""
        self._items[connector.connector_id] = connector

    # PUBLIC_INTERFACE
    def get(self, connector_id: str) -> Optional[BaseConnector]:
        """Lookup connector by id."""
        return self._items.get(connector_id)

    # PUBLIC_INTERFACE
    def all(self) -> Iterable[BaseConnector]:
        """Iterate all registered connectors."""
        return self._items.values()


registry = ConnectorRegistry()
