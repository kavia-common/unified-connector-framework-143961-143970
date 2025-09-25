"""
MongoDB collection helpers for the unified connector persistence layer.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorCollection

from src.db.mongo import mongo_db
from src.services.encryption import get_encryption_service


def _col(name: str) -> AsyncIOMotorCollection:
    return mongo_db()[name]


# PUBLIC_INTERFACE
async def upsert_connection(workspace_id: str, connector_id: str, name: str, config: Dict[str, Any]) -> str:
    """Create or update a connection record; returns connection id."""
    try:
        doc = {
            "workspace_id": workspace_id,
            "connector_id": connector_id,
            "name": name,
            "config": config,
            "updated_at": datetime.utcnow(),
        }
        result = await _col("connections").update_one(
            {"workspace_id": workspace_id, "connector_id": connector_id, "name": name},
            {"$set": doc, "$setOnInsert": {"created_at": datetime.utcnow()}},
            upsert=True,
        )
        if result.upserted_id:
            return str(result.upserted_id)
        # fetch existing id
        existing = await _col("connections").find_one(
            {"workspace_id": workspace_id, "connector_id": connector_id, "name": name},
            {"_id": 1},
        )
        return str(existing["_id"]) if existing else ""
    except Exception as e:
        print(f"Error in upsert_connection: {e}")
        return ""


# PUBLIC_INTERFACE
async def store_token(connection_id: str, token_plaintext: str, expires_at: Optional[datetime]) -> str:
    """Encrypt and store token for a connection; returns token record id."""
    enc = get_encryption_service()
    encrypted = enc.encrypt(token_plaintext)
    doc = {
        "connection_id": connection_id,
        "encrypted_token": encrypted,
        "expires_at": expires_at,
        "created_at": datetime.utcnow(),
        "rotated_at": None,
    }
    result = await _col("tokens").insert_one(doc)
    return str(result.inserted_id)


# PUBLIC_INTERFACE
async def fetch_token_plaintext(connection_id: str) -> Optional[str]:
    """Fetch latest token for a connection and decrypt; returns None if not found."""
    enc = get_encryption_service()
    doc = await _col("tokens").find_one({"connection_id": connection_id}, sort=[("created_at", -1)])
    if not doc:
        return None
    return enc.decrypt(doc["encrypted_token"])


# PUBLIC_INTERFACE
async def put_sync_state(connection_id: str, cursor: Optional[str]) -> None:
    """Upsert sync state cursor for a connection."""
    await _col("sync_states").update_one(
        {"connection_id": connection_id},
        {"$set": {"cursor": cursor, "updated_at": datetime.utcnow()}, "$setOnInsert": {"created_at": datetime.utcnow()}},
        upsert=True,
    )


# PUBLIC_INTERFACE
async def get_sync_state(connection_id: str) -> Optional[str]:
    """Get current sync cursor for a connection."""
    doc = await _col("sync_states").find_one({"connection_id": connection_id})
    return doc.get("cursor") if doc else None


# PUBLIC_INTERFACE
async def append_audit(actor: str, action: str, target_type: str, target_id: str, meta: Dict[str, Any]) -> str:
    """Append an audit log entry."""
    doc = {
        "actor": actor,
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "meta": meta,
        "created_at": datetime.utcnow(),
    }
    res = await _col("audit_logs").insert_one(doc)
    return str(res.inserted_id)
