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
    from src.db.mongo import mongo_client
    
    db_status = "unknown"
    try:
        client = mongo_client()
        # Quick ping test
        client.admin.command('ping')
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return Envelope(
        ok=True,
        data={
            "status": "running",
            "database": db_status,
            "version": "0.1.0"
        }
    )


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
