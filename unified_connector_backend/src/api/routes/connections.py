"""
Connections API routes.

Manage connection records associated to connectors, including credential persistence, validation, and revocation.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.connectors.registry import registry
from src.models.collections import (
    upsert_connection,
    store_token,
    fetch_token_plaintext,
    put_sync_state,
    get_sync_state,
    append_audit,
)
from src.models.schemas import Envelope
from src.core.errors import to_http_exception
# encryption service is available via src.services.encryption if needed in future


router = APIRouter(prefix="/connections", tags=["Connections"])


class UpsertConnectionRequest(BaseModel):
    workspaceId: str = Field(..., description="Workspace id")
    connectorId: str = Field(..., description="Connector id")
    name: str = Field(..., description="Connection name")
    config: Dict[str, Any] = Field(default_factory=dict, description="Connection configuration")

class PersistTokenRequest(BaseModel):
    connectionId: str = Field(..., description="Connection id")
    token: str = Field(..., description="Access token or API key")
    expiresAt: Optional[str] = Field(default=None, description="Optional ISO8601 expiry")

class ValidateConnectionRequest(BaseModel):
    connectionId: str = Field(..., description="Connection id")
    config: Dict[str, Any] = Field(default_factory=dict)

class RevokeConnectionRequest(BaseModel):
    connectionId: str = Field(..., description="Connection id")
    reason: Optional[str] = Field(default=None)

# PUBLIC_INTERFACE
@router.get(
    "",
    summary="List connections (scaffold)",
    response_model=Envelope,
)
async def list_connections(
    workspaceId: Optional[str] = Query(default=None, description="Filter by workspace id"),
    connectorId: Optional[str] = Query(default=None, description="Filter by connector id"),
) -> Envelope:
    """Placeholder list; real implementation would query Mongo. Returns empty list as scaffold."""
    return Envelope(ok=True, data={"items": [], "filters": {"workspaceId": workspaceId, "connectorId": connectorId}})

# PUBLIC_INTERFACE
@router.post(
    "",
    summary="Create or update a connection",
    response_model=Envelope,
)
async def upsert_connection_route(req: UpsertConnectionRequest) -> Envelope:
    """Create or update a connection record for a workspace and connector."""
    try:
        conn_id = await upsert_connection(req.workspaceId, req.connectorId, req.name, req.config)
        await append_audit(
            actor="system",
            action="upsert_connection",
            target_type="connection",
            target_id=conn_id,
            meta={"workspaceId": req.workspaceId, "connectorId": req.connectorId},
        )
        return Envelope(ok=True, data={"id": conn_id})
    except Exception as e:
        raise to_http_exception(e)

# PUBLIC_INTERFACE
@router.post(
    "/token",
    summary="Persist connection token",
    response_model=Envelope,
)
async def persist_token(req: PersistTokenRequest) -> Envelope:
    """Encrypt and store a token for a connection."""
    try:
        token_id = await store_token(req.connectionId, req.token, None)
        await append_audit(
            actor="system",
            action="store_token",
            target_type="connection",
            target_id=req.connectionId,
            meta={"tokenId": token_id},
        )
        return Envelope(ok=True, data={"tokenId": token_id})
    except Exception as e:
        raise to_http_exception(e)

# PUBLIC_INTERFACE
@router.post(
    "/validate",
    summary="Validate connection configuration via connector.validate",
    response_model=Envelope,
)
async def validate_connection(req: ValidateConnectionRequest) -> Envelope:
    """Validate the supplied connection config using connector implementation."""
    try:
        inst = registry.get(req.config.get("connectorId") or "")
        if not inst:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing or invalid connectorId in config")
        await inst.validate(req.config)
        return Envelope(ok=True, data={"valid": True})
    except Exception as e:
        raise to_http_exception(e)

# PUBLIC_INTERFACE
@router.post(
    "/revoke",
    summary="Revoke a connection (scaffold)",
    response_model=Envelope,
)
async def revoke_connection(req: RevokeConnectionRequest) -> Envelope:
    """Revoke a connection; real implementation would clean tokens and update statuses."""
    try:
        await append_audit(
            actor="system",
            action="revoke_connection",
            target_type="connection",
            target_id=req.connectionId,
            meta={"reason": req.reason},
        )
        return Envelope(ok=True, data={"revoked": True})
    except Exception as e:
        raise to_http_exception(e)

# PUBLIC_INTERFACE
@router.get(
    "/{connection_id}/token",
    summary="Fetch latest token plaintext (scaffold for internal calls)",
    response_model=Envelope,
)
async def get_token(connection_id: str) -> Envelope:
    """Return the decrypted latest token for the connection (for worker/internal use)."""
    try:
        token = await fetch_token_plaintext(connection_id)
        return Envelope(ok=True, data={"token": token})
    except Exception as e:
        raise to_http_exception(e)

# PUBLIC_INTERFACE
@router.get(
    "/{connection_id}/sync-state",
    summary="Get sync cursor",
    response_model=Envelope,
)
async def get_sync_cursor(connection_id: str) -> Envelope:
    """Return the current sync cursor for a connection."""
    try:
        cursor = await get_sync_state(connection_id)
        return Envelope(ok=True, data={"cursor": cursor})
    except Exception as e:
        raise to_http_exception(e)

# PUBLIC_INTERFACE
@router.post(
    "/{connection_id}/sync-state",
    summary="Update sync cursor",
    response_model=Envelope,
)
async def put_sync_cursor(connection_id: str, body: Dict[str, Any] = Body(default_factory=dict)) -> Envelope:
    """Update the sync cursor."""
    try:
        await put_sync_state(connection_id, body.get("cursor"))
        return Envelope(ok=True, data={"updated": True})
    except Exception as e:
        raise to_http_exception(e)
