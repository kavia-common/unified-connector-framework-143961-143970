"""
FastAPI middlewares for tenant scoping, correlation IDs, structured logging augmentation, and basic metrics hooks.
"""

import re
import time
import uuid
from typing import Callable, Awaitable, Optional, Any, Dict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .logging_config import get_logger

_logger = get_logger(__name__)

SENSITIVE_KEYS_PATTERN = re.compile(
    r"(?:^|[_\-])(?:(?:password)|(?:secret)|(?:token)|(?:api[_\-]?key)|(?:authorization)|(?:client[_\-]?secret))$",
    re.IGNORECASE,
)


def _mask_value(value: Any) -> Any:
    """
    Mask sensitive values to avoid leaking secrets in logs.
    - Strings: keep last 4 visible if length > 8, else fully mask.
    - Dict/list: recursively mask by key names matching SENSITIVE_KEYS_PATTERN.
    - Other types: return as is.
    """
    if value is None:
        return None
    if isinstance(value, str):
        if len(value) <= 8:
            return "***"
        return f"{'*' * (len(value) - 4)}{value[-4:]}"
    if isinstance(value, dict):
        return {k: ("***" if SENSITIVE_KEYS_PATTERN.search(str(k)) else _mask_value(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [_mask_value(v) for v in value]
    return value


def mask_secrets_in_body(body: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Return a deep-masked copy of a JSON-like body.
    """
    if body is None:
        return None
    return _mask_value(body)


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that extracts tenant_id from X-Tenant-Id header and sets it on request.state.tenant_id.

    It also:
    - Extracts/creates a correlation_id (from X-Request-Id or X-Correlation-Id) and assigns to request.state.correlation_id.
    - Measures request duration and logs a structured line on completion (without leaking sensitive data).
    - Increments simple in-memory error counts placeholder (can be replaced by Prometheus client).
    """

    def __init__(self, app, api_tag_header: str = "X-Api-Tag") -> None:
        super().__init__(app)
        self.api_tag_header = api_tag_header
        # Basic in-memory counters (placeholder for real metrics)
        self._error_count = 0

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Extract tenant and correlation
        headers = request.headers
        tenant_id = headers.get("X-Tenant-Id")
        correlation_id = headers.get("X-Request-Id") or headers.get("X-Correlation-Id") or str(uuid.uuid4())
        api_tag = headers.get(self.api_tag_header)
        # Attach to request.state
        request.state.tenant_id = tenant_id
        request.state.correlation_id = correlation_id
        request.state.api_tag = api_tag

        # Timing
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as exc:
            # Increment error counter placeholder
            self._error_count += 1
            _logger.exception("Unhandled error for request")
            raise exc
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)

            # Log with context. Avoid reading the body stream to not consume it.
            # We log method, path, status, duration, tenant_id, api_tag, correlation_id.
            extra = {
                "request_id": correlation_id,
                "tenant_id": tenant_id,
                "api_tag": api_tag,
                "duration_ms": duration_ms,
                "status_code": status_code,
                "path": request.url.path,
                "method": request.method,
                # Basic metric hooks
                "metrics": {
                    "request_time_ms": duration_ms,
                    "error_count": self._error_count,
                },
            }
            # Add query params (non-sensitive)
            if request.query_params:
                extra["query_params"] = dict(request.query_params.items())

            # Add limited, masked headers for debugging (exclude Authorization and cookies)
            safe_headers: Dict[str, str] = {}
            for k, v in headers.items():
                if k.lower() in ("authorization", "cookie", "set-cookie"):
                    continue
                # Some headers might contain tokens (e.g., x-api-key); mask those
                safe_headers[k] = "***" if SENSITIVE_KEYS_PATTERN.search(k) else v
            extra["headers"] = safe_headers

            # Emit structured log
            _logger.info("request_completed", extra=extra)


# PUBLIC_INTERFACE
def get_tenant_id(request: Request) -> Optional[str]:
    """Return the tenant id extracted by TenantContextMiddleware, if available."""
    return getattr(request.state, "tenant_id", None)


# PUBLIC_INTERFACE
def get_correlation_id(request: Request) -> Optional[str]:
    """Return the correlation id attached to the request context."""
    return getattr(request.state, "correlation_id", None)
