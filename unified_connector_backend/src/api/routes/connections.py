"""
Connections API routes.

Manage connection records associated to connectors.
"""

from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.models.collections import upsert_connection
from src.models.schemas import Envelope


router = APIRouter(prefix="/connections", tags=["Connections"])


class UpsertConnectionRequest(BaseModel):
    workspaceId: str = Field(..., description="Workspace id")
    connectorId: str = Field(..., description="Connector id")
    name: str = Field(..., description="Connection name")
    config: Dict[str, Any] = Field(default_factory=dict, description="Connection configuration")


# PUBLIC_INTERFACE
@router.post(
    "",
    summary="Create or update a connection",
    response_model=Envelope,
)
async def upsert_connection_route(req: UpsertConnectionRequest) -> Envelope:
    """Create or update a connection record for a workspace and connector."""
    conn_id = await upsert_connection(req.workspaceId, req.connectorId, req.name, req.config)
    return Envelope(ok=True, data={"id": conn_id})
