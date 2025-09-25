"""
MongoDB client factory and FastAPI lifecycle integration.
"""

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from src.core.config import get_settings


_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


# PUBLIC_INTERFACE
def mongo_client() -> AsyncIOMotorClient:
    """Return a singleton AsyncIOMotorClient instance."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncIOMotorClient(settings.MONGODB_URL.unicode_string())
    return _client


# PUBLIC_INTERFACE
def mongo_db() -> AsyncIOMotorDatabase:
    """Return the configured MongoDB database handle."""
    global _db
    if _db is None:
        _db = mongo_client()[get_settings().MONGODB_DB]
    return _db


# PUBLIC_INTERFACE
async def close_mongo_client() -> None:
    """Close the MongoDB client if initialized."""
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None
