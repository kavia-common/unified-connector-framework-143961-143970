"""
Logging configuration utilities with structured JSON logging and context enrichment.
"""

import json
import logging
import sys
from typing import Optional

from .config import get_settings


class RequestContextFilter(logging.Filter):
    """
    A logging filter that ensures presence of common contextual fields.
    Allows code to pass extra={...} without failing if not present.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        # Normalize expected keys for JSON logs
        if not hasattr(record, "request_id"):
            record.request_id = None  # correlation id
        if not hasattr(record, "tenant_id"):
            record.tenant_id = None
        if not hasattr(record, "api_tag"):
            record.api_tag = None
        return True


class JsonFormatter(logging.Formatter):
    """JSON formatter for logs with request context."""

    def format(self, record: logging.LogRecord) -> str:
        log_dict = {
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "time": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
            "request_id": getattr(record, "request_id", None),
            "tenant_id": getattr(record, "tenant_id", None),
            "api_tag": getattr(record, "api_tag", None),
        }
        # Allow arbitrary extra fields (e.g., metrics)
        for key in ("duration_ms", "status_code", "path", "method", "headers", "query_params", "metrics"):
            if hasattr(record, key):
                log_dict[key] = getattr(record, key)
        if record.exc_info:
            log_dict["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_dict, ensure_ascii=False)


def configure_logging() -> None:
    """Configure root logger based on settings."""
    settings = get_settings()
    root = logging.getLogger()
    root.setLevel(settings.LOG_LEVEL.upper())
    # Clear default handlers installed by uvicorn
    for h in list(root.handlers):
        root.removeHandler(h)
    handler = logging.StreamHandler(sys.stdout)
    if settings.LOG_JSON:
        handler.setFormatter(JsonFormatter())
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s | request_id=%(request_id)s tenant_id=%(tenant_id)s api_tag=%(api_tag)s"
        )
        handler.setFormatter(formatter)
    handler.addFilter(RequestContextFilter())
    root.addHandler(handler)


# PUBLIC_INTERFACE
def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a configured logger."""
    return logging.getLogger(name or __name__)
