"""
Health and informational routes.
"""

from fastapi import APIRouter
from src.models.schemas import Envelope

router = APIRouter(tags=["Health"])


# PUBLIC_INTERFACE
@router.get("/", summary="Health Check")
def health_check() -> Envelope:
    """Basic health check endpoint."""
    return Envelope(ok=True, data={"message": "Healthy"})


# PUBLIC_INTERFACE
@router.get(
    "/ws/docs",
    summary="WebSocket Usage",
    description="This API will expose WebSocket endpoints for job progress in future iterations. Connect to /ws for multiplexed job updates.",
    tags=["WebSocket"],
)
def websocket_help() -> Envelope:
    """Provide guidance for connecting to WebSockets for real-time job status."""
    return Envelope(
        ok=True,
        data={
            "websocket": {
                "endpoint": "/ws",
                "notes": "Subscribe with {type:'job_progress', jobId:'...'} frames to receive updates.",
            }
        },
    )
