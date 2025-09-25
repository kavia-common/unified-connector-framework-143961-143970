"""
FastAPI API package initializer.

Exposes routers package for route discovery and ensures connectors are registered.
"""

try:
    # Try to import connectors but don't block startup if it fails
    import src.connectors  # noqa: F401
except Exception as e:
    print(f"Warning: Failed to initialize connectors: {e}")

# Export routes subpackage
from . import routes  # noqa: F401
