from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import get_settings
from src.core.logging_config import configure_logging
from src.core.middleware import TenantContextMiddleware
from src.db.mongo import close_mongo_client
from .routes.health import router as health_router
from .routes.connectors import router as connectors_router
from .routes.connections import router as connections_router

# Configure logging early
configure_logging()

settings = get_settings()

openapi_tags = [
    {"name": "Health", "description": "Service health endpoints"},
    {
        "name": "Connectors",
        "description": "Manage connectors and start jobs. All requests should include X-Tenant-Id and optional X-Request-Id for correlation.",
    },
    {
        "name": "Connections",
        "description": "Manage connections and credentials. Include X-Tenant-Id to scope to tenant.",
    },
    {"name": "WebSocket", "description": "Real-time WebSocket/SSE documentation"},
]

app = FastAPI(
    **settings.app_metadata(),
    openapi_tags=openapi_tags,
)

# Tenant and observability middleware
app.add_middleware(TenantContextMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


@app.on_event("startup")
async def _on_startup():
    print("Starting API initialization...")
    
    # Test MongoDB connection but don't fail startup
    try:
        from src.db.mongo import mongo_client
        client = mongo_client()
        client.admin.command('ping')
        print("MongoDB connection successful")
    except Exception as e:
        print(f"Warning: MongoDB connection failed: {e}")
        print("API will start but database operations will be unavailable")

    # Register connectors lazily
    try:
        from src.connectors import register_connectors
        if register_connectors():
            print("Connector registration successful")
        else:
            print("Warning: Some connectors failed to register")
    except Exception as e:
        print(f"Warning: Failed to register connectors: {e}")
        print("API will start with limited connector functionality")

@app.on_event("shutdown")
async def _on_shutdown():
    await close_mongo_client()

# Mount routers
app.include_router(health_router)
app.include_router(connectors_router, prefix=settings.API_PREFIX)
app.include_router(connections_router, prefix=settings.API_PREFIX)
