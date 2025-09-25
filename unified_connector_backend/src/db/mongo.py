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
        print(f"Initializing MongoDB connection to {settings.MONGODB_URL}")
        try:
            _client = AsyncIOMotorClient(
                settings.MONGODB_URL.unicode_string(),
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
                waitQueueTimeoutMS=5000,
                connect=False  # Don't connect immediately
            )
            # Try to establish connection
            print("Testing MongoDB connection...")
            _client.admin.command('ping')
            print("MongoDB connection successful")
        except Exception as e:
            print(f"Warning: MongoDB connection failed: {str(e)}")
            # Initialize client without connecting for retry later
            _client = AsyncIOMotorClient(
                settings.MONGODB_URL.unicode_string(),
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
                connect=False
            )
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
