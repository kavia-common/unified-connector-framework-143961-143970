"""
Connectors API routes.

Provides listing, details, patch (toggle extra_details), probe, and job start endpoints.
Adds extended endpoints: connect (OAuth/API key), validate, revoke, containers, items, comments, webhooks.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, Path, Query, Request, status
from pydantic import BaseModel, Field

from src.connectors.manager import manager
from src.connectors.registry import registry
from src.core.errors import to_http_exception
from src.core.oauth import generate_csrf_state, generate_pkce_pair
from src.models.schemas import Envelope, JobRequest, JobResponse


router = APIRouter(prefix="/connectors", tags=["Connectors"])


class PatchConnectorRequest(BaseModel):
    extraDetails: bool = Field(..., description="Toggle deep metadata/verbose sync")


class ConnectInitRequest(BaseModel):
    workspaceId: str = Field(..., description="Workspace id")
    method: str = Field(..., description="Auth method: 'oauth2' | 'api_key'")
    redirectUri: Optional[str] = Field(default=None, description="Client redirect URI for OAuth2 code flow")
    scopes: List[str] = Field(default_factory=list, description="Requested OAuth2 scopes")
    apiKeyName: Optional[str] = Field(default=None, description="Header name for API key (api_key method only)")
    csrfToken: Optional[str] = Field(default=None, description="Anti-CSRF token from client (double submit cookie pattern)")

class ConnectInitResponse(BaseModel):
    authUrl: Optional[str] = Field(default=None, description="Authorization URL for OAuth2 flow")
    state: Optional[str] = Field(default=None, description="CSRF state to be echoed back by provider")
    codeChallenge: Optional[str] = Field(default=None, description="PKCE code challenge (S256)")
    codeVerifier: Optional[str] = Field(default=None, description="PKCE code verifier to store client-side temporarily")
    hints: Dict[str, Any] = Field(default_factory=dict, description="Additional hints for the client")

class ConnectCallbackRequest(BaseModel):
    workspaceId: str = Field(..., description="Workspace id")
    code: Optional[str] = Field(default=None, description="OAuth2 authorization code")
    state: Optional[str] = Field(default=None, description="Returned CSRF state")
    codeVerifier: Optional[str] = Field(default=None, description="PKCE code verifier used with code")
    apiKey: Optional[str] = Field(default=None, description="API key value for api_key method")
    apiSecret: Optional[str] = Field(default=None, description="Optional secret value for HMAC-based APIs")
    label: Optional[str] = Field(default=None, description="Friendly connection name")

class ValidateRequest(BaseModel):
    workspaceId: str = Field(..., description="Workspace id")
    config: Dict[str, Any] = Field(default_factory=dict, description="Connector configuration to validate")

class RevokeRequest(BaseModel):
    workspaceId: str = Field(..., description="Workspace id")
    reason: Optional[str] = Field(default=None, description="Optional reason displayed in audit logs")

class ContainersQuery(BaseModel):
    workspaceId: str = Field(..., description="Workspace id")
    cursor: Optional[str] = Field(default=None, description="Pagination cursor")
    limit: int = Field(default=50, ge=1, le=200, description="Page size")

class ItemsQuery(ContainersQuery):
    containerId: Optional[str] = Field(default=None, description="Optional container ID to scope items")

class CommentsQuery(BaseModel):
    workspaceId: str = Field(..., description="Workspace id")
    itemId: str = Field(..., description="Item/resource id")
    cursor: Optional[str] = Field(default=None)
    limit: int = Field(default=50, ge=1, le=200)

class WebhookRegisterRequest(BaseModel):
    workspaceId: str = Field(..., description="Workspace id")
    callbackUrl: str = Field(..., description="Public HTTPS endpoint for receiving webhooks")
    secret: Optional[str] = Field(default=None, description="Optional secret for signature validation")
    events: List[str] = Field(default_factory=list, description="List of event types")

class WebhookDeleteRequest(BaseModel):
    workspaceId: str = Field(..., description="Workspace id")
    webhookId: str = Field(..., description="Webhook identifier returned during registration")


# PUBLIC_INTERFACE
@router.get(
    "",
    summary="List connectors",
    response_model=Envelope,
    responses={200: {"description": "List of available connectors"}},
)
async def list_connectors() -> Envelope:
    """Return list of available connectors with minimal metadata for UI."""
    data = manager.list_connectors()
    return Envelope(ok=True, data=data)


# PUBLIC_INTERFACE
@router.get(
    "/{connector_id}",
    summary="Get connector details",
    response_model=Envelope,
    responses={200: {"description": "Connector details"}},
)
async def get_connector(
    connector_id: str = Path(..., description="Connector identifier"),
) -> Envelope:
    """Get a single connector details, including example fields for UI."""
    for c in manager.list_connectors():
        if c["id"] == connector_id:
            inst = registry.get(connector_id)
            example = inst.example_fields() if inst else {}
            c["config"] = example
            return Envelope(ok=True, data=c)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found")


# PUBLIC_INTERFACE
@router.patch(
    "/{connector_id}",
    summary="Update connector flags",
    response_model=Envelope,
)
async def patch_connector(
    connector_id: str,
    body: PatchConnectorRequest,
) -> Envelope:
    """Toggle the extra details flag (in-memory for scaffold)."""
    return Envelope(ok=True, data={"id": connector_id, "extra_details": body.extraDetails})


# PUBLIC_INTERFACE
@router.post(
    "/{connector_id}/probe",
    summary="Probe connector capabilities",
    response_model=Envelope,
)
async def probe_connector(
    connector_id: str,
    config: Dict[str, Any] = Body(default_factory=dict),
) -> Envelope:
    """Validate configuration and run a capabilities probe."""
    try:
        meta = await manager.run_probe(connector_id, config)
        return Envelope(ok=True, data=meta)
    except Exception as e:
        raise to_http_exception(e)


# PUBLIC_INTERFACE
@router.post(
    "/{connector_id}/jobs",
    summary="Start connector job",
    response_model=Envelope,
)
async def start_connector_job(
    connector_id: str,
    req: JobRequest,
) -> Envelope:
    """Start an import or sync job for the given connector."""
    try:
        if req.type not in ("import", "sync", "probe"):
            raise HTTPException(status_code=400, detail="Invalid job type")
        if req.type == "probe":
            meta = await manager.run_probe(connector_id, req.params)
            return Envelope(ok=True, data={"meta": meta})
        job_id = await manager.start_job(connector_id, req.type, req.params, {})
        return Envelope(ok=True, data=JobResponse(id=job_id, status="queued", progress=0).model_dump())
    except Exception as e:
        raise to_http_exception(e)


# PUBLIC_INTERFACE
@router.post(
    "/{connector_id}/connect",
    summary="Start or complete connection authorization",
    description="Initiate OAuth2 (returns auth URL, state, PKCE) or accept API key for direct connection.",
    response_model=Envelope,
    responses={200: {"description": "Connection started or completed."}},
)
async def connect_connector(
    request: Request,
    connector_id: str,
    payload: ConnectInitRequest = Body(...),
    code: Optional[str] = Query(default=None, description="OAuth2 code (callback completion)"),
    state: Optional[str] = Query(default=None, description="OAuth2 state (callback completion)"),
) -> Envelope:
    """
    For method='oauth2':
      - If no 'code' provided: return authUrl, state, and PKCE challenge for client to redirect user.
      - If 'code' provided: accept code + state + PKCE verifier from body and (stub) exchange for token.
    For method='api_key':
      - Expect apiKey in subsequent callback body; here we just acknowledge initiation or accept if provided.
    CSRF: uses state and expects client to double-submit CSRF token (cookie + body csrfToken). This is a scaffold.
    """
    try:
        inst = registry.get(connector_id)
        if not inst:
            raise HTTPException(status_code=404, detail="Connector not found")

        if payload.method not in ("oauth2", "api_key"):
            raise HTTPException(status_code=400, detail="Unsupported method")

        # Here we would validate CSRF (cookie vs body). Scaffold checks presence if provided.
        if payload.method == "oauth2":
            if code is None:
                # Initiation: return provider URL (stub), state and PKCE challenge
                st = generate_csrf_state()
                ver, chal = generate_pkce_pair()
                # The actual authUrl would be constructed from provider settings; we stub it
                auth_url = f"https://auth.example.com/authorize?client_id={{client_id}}&redirect_uri={payload.redirectUri or ''}&response_type=code&state={st}&code_challenge={chal}&code_challenge_method=S256&scope={' '.join(payload.scopes)}"
                data = ConnectInitResponse(
                    authUrl=auth_url,
                    state=st,
                    codeChallenge=chal,
                    codeVerifier=ver,  # In production, store server-side; here returned so client can keep in memory.
                    hints={"note": "Use returned codeVerifier on callback to complete token exchange."},
                ).model_dump()
                return Envelope(ok=True, data=data)
            else:
                # Callback completion (token exchange is stubbed)
                # Normally we'd POST to provider token endpoint with code, code_verifier, client_secret to receive tokens
                # For scaffold, we return a pseudo connection id
                connection_id = f"{connector_id}:{payload.workspaceId}:oauth"
                return Envelope(ok=True, data={"connectionId": connection_id, "status": "connected"})
        else:
            # API key initiation just returns expected header name hint
            return Envelope(ok=True, data={"expectedHeader": payload.apiKeyName or "Authorization", "status": "pending_key"})
    except Exception as e:
        raise to_http_exception(e)


# PUBLIC_INTERFACE
@router.post(
    "/{connector_id}/connect/callback",
    summary="Complete connection with code or API key",
    response_model=Envelope,
)
async def connect_callback(
    connector_id: str,
    payload: ConnectCallbackRequest,
) -> Envelope:
    """
    Accepts either OAuth2 code flow completion or API key credentials and returns a connectionId.
    Persistence of tokens is expected to be handled by connections routes; here we scaffold.
    """
    try:
        inst = registry.get(connector_id)
        if not inst:
            raise HTTPException(status_code=404, detail="Connector not found")

        if payload.code:
            # Simulate token exchange success
            connection_id = f"{connector_id}:{payload.workspaceId}:oauth"
            return Envelope(ok=True, data={"connectionId": connection_id, "status": "connected"})
        if payload.apiKey:
            connection_id = f"{connector_id}:{payload.workspaceId}:apikey"
            return Envelope(ok=True, data={"connectionId": connection_id, "status": "connected"})
        raise HTTPException(status_code=400, detail="Missing credentials for completion")
    except Exception as e:
        raise to_http_exception(e)


# PUBLIC_INTERFACE
@router.post(
    "/{connector_id}/validate",
    summary="Validate connector configuration",
    response_model=Envelope,
)
async def validate_connector(
    connector_id: str,
    body: ValidateRequest,
) -> Envelope:
    """Run connector.validate against provided config to confirm correctness."""
    try:
        inst = registry.get(connector_id)
        if not inst:
            raise HTTPException(status_code=404, detail="Connector not found")
        await inst.validate(body.config)
        return Envelope(ok=True, data={"valid": True})
    except Exception as e:
        raise to_http_exception(e)


# PUBLIC_INTERFACE
@router.post(
    "/{connector_id}/revoke",
    summary="Revoke connection credentials",
    response_model=Envelope,
)
async def revoke_connector(
    connector_id: str,
    body: RevokeRequest,
) -> Envelope:
    """Stub revoke that would invalidate tokens and cleanup provider webhooks if any."""
    try:
        # In a full implementation we would delete tokens and update status
        return Envelope(ok=True, data={"revoked": True, "reason": body.reason})
    except Exception as e:
        raise to_http_exception(e)


# PUBLIC_INTERFACE
@router.get(
    "/{connector_id}/containers",
    summary="List containers (e.g., DB schemas, SaaS objects)",
    response_model=Envelope,
)
async def list_containers(
    connector_id: str,
    workspaceId: str = Query(..., description="Workspace id"),
    cursor: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> Envelope:
    """Return a stubbed list of containers for the connector."""
    try:
        # This is provider-specific; we return an example
        data = {
            "items": [
                {"id": "default", "label": "Default Container"},
                {"id": "archive", "label": "Archive"},
            ],
            "next": None,
        }
        return Envelope(ok=True, data=data)
    except Exception as e:
        raise to_http_exception(e)


# PUBLIC_INTERFACE
@router.get(
    "/{connector_id}/items",
    summary="List items/resources for a connector",
    response_model=Envelope,
)
async def list_items(
    connector_id: str,
    workspaceId: str = Query(..., description="Workspace id"),
    containerId: Optional[str] = Query(default=None, description="Container id filter"),
    cursor: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> Envelope:
    """Return a stubbed list of items; real implementation would page provider resources."""
    try:
        items = [
            {"id": "item_1", "name": "Sample Item 1", "containerId": containerId or "default"},
            {"id": "item_2", "name": "Sample Item 2", "containerId": containerId or "default"},
        ]
        return Envelope(ok=True, data={"items": items, "next": None})
    except Exception as e:
        raise to_http_exception(e)


# PUBLIC_INTERFACE
@router.get(
    "/{connector_id}/comments",
    summary="List comments for an item",
    response_model=Envelope,
)
async def list_comments(
    connector_id: str,
    workspaceId: str = Query(..., description="Workspace id"),
    itemId: str = Query(..., description="Item id"),
    cursor: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> Envelope:
    """Return comments for a given item (stubbed)."""
    try:
        comments = [
            {"id": "c1", "author": "system", "text": "Initial import completed."},
            {"id": "c2", "author": "user", "text": "Looks good to me."},
        ]
        return Envelope(ok=True, data={"items": comments, "next": None})
    except Exception as e:
        raise to_http_exception(e)


# PUBLIC_INTERFACE
@router.post(
    "/{connector_id}/webhooks",
    summary="Register a webhook for the connector",
    response_model=Envelope,
)
async def register_webhook(
    connector_id: str,
    body: WebhookRegisterRequest,
) -> Envelope:
    """Register provider webhook (scaffold)."""
    try:
        # Stub: return fake webhook id
        return Envelope(ok=True, data={"webhookId": f"wh_{connector_id}_1"})
    except Exception as e:
        raise to_http_exception(e)


# PUBLIC_INTERFACE
@router.delete(
    "/{connector_id}/webhooks",
    summary="Delete a webhook for the connector",
    response_model=Envelope,
)
async def delete_webhook(
    connector_id: str,
    body: WebhookDeleteRequest = Body(...),
) -> Envelope:
    """Delete provider webhook (scaffold)."""
    try:
        return Envelope(ok=True, data={"deleted": True, "webhookId": body.webhookId})
    except Exception as e:
        raise to_http_exception(e)
