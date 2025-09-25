"""
Connector manager orchestrates operations over the registry.
"""

from typing import Any, Dict, List, Literal

from src.core.logging_config import get_logger
from .registry import registry
from .base import BaseConnector

_logger = get_logger(__name__)


class ConnectorManager:
    """High-level operations on connectors."""

    # PUBLIC_INTERFACE
    def list_connectors(self) -> List[Dict[str, Any]]:
        """Return minimal connector info for UI listing."""
        result = []
        for c in registry.all():
            result.append(
                {
                    "id": c.connector_id,
                    "group": c.group,
                    "name": c.name,
                    "status": "not_connected",  # default; real status resolved per workspace/connection
                    "meta": {},
                    "config": {},
                    "extra_details": False,
                }
            )
        return result

    # PUBLIC_INTERFACE
    async def run_probe(self, connector_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate then run probe for capabilities metadata."""
        connector = self._require(connector_id)
        await connector.validate(config)
        meta = await connector.probe(config)
        return meta

    # PUBLIC_INTERFACE
    async def start_job(
        self, connector_id: str, job_type: Literal["import", "sync"], config: Dict[str, Any], params: Dict[str, Any]
    ) -> str:
        """Validate config and start a job through the connector implementation."""
        connector = self._require(connector_id)
        await connector.validate(config)
        job_id = await connector.execute(job_type, config, params)
        _logger.info(f"Started job {job_id} for {connector_id} type={job_type}")
        return job_id

    def _require(self, connector_id: str) -> BaseConnector:
        c = registry.get(connector_id)
        if not c:
            raise ValueError(f"Connector '{connector_id}' not found")
        return c


manager = ConnectorManager()
