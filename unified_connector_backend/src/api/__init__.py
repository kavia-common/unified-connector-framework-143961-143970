"""
FastAPI API package initializer.

Exposes routers package for route discovery and ensures connectors are registered.
"""

# Ensure example connectors register at import time for development scaffolding
import src.connectors  # noqa: F401

# Export routes subpackage
from . import routes  # noqa: F401
