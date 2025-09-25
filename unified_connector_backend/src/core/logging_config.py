"""
Logging configuration utilities.
"""

import json
import logging
import sys
from typing import Optional

from .config import get_settings


class JsonFormatter(logging.Formatter):
    """JSON formatter for logs."""

    def format(self, record: logging.LogRecord) -> str:
        log_dict = {
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "time": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
        }
        if hasattr(record, "request_id"):
            log_dict["request_id"] = getattr(record, "request_id")
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
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        handler.setFormatter(formatter)
    root.addHandler(handler)


# PUBLIC_INTERFACE
def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a configured logger."""
    return logging.getLogger(name or __name__)
