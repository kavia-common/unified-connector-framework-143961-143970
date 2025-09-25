"""
Error normalization utilities and unified envelope helpers.
"""

from typing import Any, Dict, Optional, Tuple
from fastapi import HTTPException, status
from pydantic import BaseModel, Field

# PUBLIC_INTERFACE
class UnifiedError(BaseModel):
    """Normalized error payload"""
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Optional extra details")


# PUBLIC_INTERFACE
def to_http_exception(exc: Exception) -> HTTPException:
    """Map arbitrary exceptions to HTTPException with normalized structure."""
    if isinstance(exc, HTTPException):
        return exc
    code, status_code = _map_error(exc)
    return HTTPException(
        status_code=status_code,
        detail=UnifiedError(code=code, message=str(exc)).model_dump(),
    )


def _map_error(exc: Exception) -> Tuple[str, int]:
    text = str(exc).lower()
    if "not found" in text:
        return "not_found", status.HTTP_404_NOT_FOUND
    if "unauthorized" in text or "forbidden" in text or "permission" in text:
        return "forbidden", status.HTTP_403_FORBIDDEN
    if "invalid" in text or "missing" in text or "bad request" in text:
        return "invalid_request", status.HTTP_400_BAD_REQUEST
    if "conflict" in text or "already exists" in text:
        return "conflict", status.HTTP_409_CONFLICT
    if "timeout" in text:
        return "timeout", status.HTTP_504_GATEWAY_TIMEOUT
    return "internal_error", status.HTTP_500_INTERNAL_SERVER_ERROR
