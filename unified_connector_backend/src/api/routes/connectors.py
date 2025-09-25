"""
Connectors API routes.

Provides listing, details, patch (toggle extra_details), probe, and job start endpoints.
"""

from typing import Any, Dict

from fastapi import APIRouter, Body, HTTPException, Path, status
from pydantic import BaseModel, Field

from src.connectors.manager import manager
from src.models.schemas import Envelope, JobRequest, JobResponse


router = APIRouter(prefix="/connectors", tags=["Connectors"])


class PatchConnectorRequest(BaseModel):
    extraDetails: bool = Field(..., description="Toggle deep metadata/verbose sync")


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
    # In this initial scaffold, pull from listing and add example fields
    for c in manager.list_connectors():
        if c["id"] == connector_id:
            # best-effort example fields
            from src.connectors.registry import registry
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
    # Stateless scaffold: echo back
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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


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
    if req.type not in ("import", "sync", "probe"):
        raise HTTPException(status_code=400, detail="Invalid job type")
    if req.type == "probe":
        meta = await manager.run_probe(connector_id, req.params)
        return Envelope(ok=True, data={"meta": meta})
    job_id = await manager.start_job(connector_id, req.type, req.params, {})
    return Envelope(ok=True, data=JobResponse(id=job_id, status="queued", progress=0).model_dump())
