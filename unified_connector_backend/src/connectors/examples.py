"""
Example connector stubs to demonstrate registry usage.
These are placeholders; real implementations will connect to providers.
"""

import asyncio
import uuid
from typing import Any, Dict, Literal

from .base import BaseConnector
from .registry import registry


class PostgresConnector(BaseConnector):
    def __init__(self) -> None:
        super().__init__("postgres", "db", "PostgreSQL")

    async def validate(self, config: Dict[str, Any]) -> None:
        required = ["host", "port"]
        missing = [k for k in required if k not in config]
        if missing:
            raise ValueError(f"Missing config fields: {', '.join(missing)}")

    async def probe(self, config: Dict[str, Any]) -> Dict[str, Any]:
        # Simulate capability probe
        return {"apiPid": "same", "fields": {"host": config.get("host"), "port": config.get("port")}}

    async def execute(self, job_type: Literal["import", "sync"], config: Dict[str, Any], params: Dict[str, Any]) -> str:
        # Simulate async job creation
        await asyncio.sleep(0.01)
        return str(uuid.uuid4())

    def example_fields(self) -> Dict[str, Any]:
        return {"host": "db.example.com", "port": 5432}


class SalesforceConnector(BaseConnector):
    def __init__(self) -> None:
        super().__init__("salesforce", "saas", "Salesforce")

    async def validate(self, config: Dict[str, Any]) -> None:
        # For OAuth connectors minimal config may be empty; token gate happens elsewhere
        return None

    async def probe(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"scopes": ["api", "refresh_token"], "instance": config.get("instance")}

    async def execute(self, job_type: Literal["import", "sync"], config: Dict[str, Any], params: Dict[str, Any]) -> str:
        return str(uuid.uuid4())

    def example_fields(self) -> Dict[str, Any]:
        return {"instance": "https://my-instance.my.salesforce.com"}


# Register example connectors at import time
registry.register(PostgresConnector())
registry.register(SalesforceConnector())
