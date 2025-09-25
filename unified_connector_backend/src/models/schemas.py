"""
Pydantic models for API requests and responses, aligned with Unified Connector Framework envelope.
"""

from datetime import datetime
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field


class Envelope(BaseModel):
    """Standard response envelope."""
    ok: bool = Field(..., description="Operation status")
    data: Optional[Any] = Field(default=None, description="Payload")
    error: Optional[str] = Field(default=None, description="Error message if any")


class Connector(BaseModel):
    id: str = Field(..., description="Connector identifier (e.g., 'postgres', 'salesforce')")
    group: Literal["db", "saas"] = Field(..., description="Connector group")
    name: str = Field(..., description="Human friendly name")
    status: Literal["connected", "not_connected", "error"] = Field(..., description="Connection status")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Connector metadata like API PID or scopes")
    config: Dict[str, Any] = Field(default_factory=dict, description="Connector configuration")
    extra_details: bool = Field(default=False, description="Enable deep metadata or verbose sync")
    workspace_id: Optional[str] = Field(default=None, description="Owning workspace id")
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)


class ConnectionRecord(BaseModel):
    id: str = Field(..., description="Connection id (uuid)")
    connector_id: str = Field(..., description="Connector id this connection is for")
    workspace_id: str = Field(..., description="Workspace id")
    name: str = Field(..., description="Display name for this connection")
    config: Dict[str, Any] = Field(default_factory=dict, description="Connection config (host, port, etc.)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TokenRecord(BaseModel):
    id: str = Field(..., description="Token id")
    connection_id: str = Field(..., description="Associated connection id")
    encrypted_token: str = Field(..., description="Encrypted token (Fernet)")
    expires_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    rotated_at: Optional[datetime] = Field(default=None)


class SyncStateRecord(BaseModel):
    id: str = Field(..., description="Sync state id")
    connection_id: str = Field(..., description="Associated connection id")
    cursor: Optional[str] = Field(default=None, description="Provider-specific cursor/offset")
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AuditLogRecord(BaseModel):
    id: str = Field(..., description="Audit log id")
    actor: str = Field(..., description="User or system actor")
    action: str = Field(..., description="Action performed")
    target_type: str = Field(..., description="Target type (connector, connection, job)")
    target_id: str = Field(..., description="Target identifier")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Additional details")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class JobRequest(BaseModel):
    type: Literal["import", "sync", "probe"] = Field(..., description="Job type to start")
    params: Dict[str, Any] = Field(default_factory=dict, description="Optional parameters")


class JobResponse(BaseModel):
    id: str = Field(..., description="Job id")
    status: Literal["queued", "running", "succeeded", "failed", "canceled"] = Field(..., description="Job status")
    progress: int = Field(default=0, ge=0, le=100)
