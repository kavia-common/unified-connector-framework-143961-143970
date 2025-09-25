from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import get_settings
from src.core.logging_config import configure_logging
from src.db.mongo import close_mongo_client
from .routes.health import router as health_router
from .routes.connectors import router as connectors_router
from .routes.connections import router as connections_router

# Configure logging early
configure_logging()

settings = get_settings()

openapi_tags = [
    {"name": "Health", "description": "Service health endpoints"},
    {"name": "Connectors", "description": "Manage connectors and start jobs"},
    {"name": "Connections", "description": "Manage connections and credentials"},
    {"name": "WebSocket", "description": "Real-time WebSocket/SSE documentation"},
]

app = FastAPI(
    **settings.app_metadata(),
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


@app.on_event("shutdown")
async def _on_shutdown():
    await close_mongo_client()


# Mount routers
app.include_router(health_router)
app.include_router(connectors_router, prefix=settings.API_PREFIX)
app.include_router(connections_router, prefix=settings.API_PREFIX)
