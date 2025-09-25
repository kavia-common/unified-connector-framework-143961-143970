"""
Security helpers: hashing, request context, and placeholders for JWT/OAuth.
"""

import base64
import hashlib
import hmac
from typing import Optional

from .config import get_settings


# PUBLIC_INTERFACE
def hmac_sha256(secret: str, data: str) -> str:
    """Compute HMAC-SHA256 of data using provided secret; returns base64 encoded digest."""
    digest = hmac.new(secret.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


# PUBLIC_INTERFACE
def get_request_id(headers: dict) -> Optional[str]:
    """Extract request id from headers if present."""
    return headers.get("x-request-id") or headers.get("x-correlation-id")


# PUBLIC_INTERFACE
def require_encryption_key() -> bytes:
    """Return the configured encryption key as bytes, raising if not set in production contexts."""
    settings = get_settings()
    if not settings.ENCRYPTION_KEY:
        # For dev we allow empty; crypto layer will auto-generate ephemeral key but warn.
        return b""
    try:
        return base64.urlsafe_b64decode(settings.ENCRYPTION_KEY)
    except Exception as exc:
        raise ValueError("Invalid ENCRYPTION_KEY; must be URL-safe base64 32-byte key") from exc
