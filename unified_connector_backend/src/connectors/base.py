"""
Connector base class defining required interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Literal


class BaseConnector(ABC):
    """Abstract connector interface for DB/SaaS providers."""

    connector_id: str
    group: Literal["db", "saas"]
    name: str

    def __init__(self, connector_id: str, group: Literal["db", "saas"], name: str) -> None:
        self.connector_id = connector_id
        self.group = group
        self.name = name

    # PUBLIC_INTERFACE
    @abstractmethod
    async def validate(self, config: Dict[str, Any]) -> None:
        """Validate configuration and raise ValueError on failure."""

    # PUBLIC_INTERFACE
    @abstractmethod
    async def probe(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Probe provider for capabilities/metadata."""

    # PUBLIC_INTERFACE
    @abstractmethod
    async def execute(self, job_type: Literal["import", "sync"], config: Dict[str, Any], params: Dict[str, Any]) -> str:
        """Start a job and return a job id."""

    # PUBLIC_INTERFACE
    def example_fields(self) -> Dict[str, Any]:
        """Return example fields to display in UI."""
        return {}
