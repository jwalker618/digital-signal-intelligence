"""
DSI Structured Logging Configuration

Provides JSON-formatted logs with correlation IDs for production
and human-readable logs for development.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Optional


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured log aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add correlation ID if present
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id

        # Add extra fields
        if hasattr(record, "entity_id"):
            log_entry["entity_id"] = record.entity_id
        if hasattr(record, "coverage"):
            log_entry["coverage"] = record.coverage
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms
        if hasattr(record, "signal_id"):
            log_entry["signal_id"] = record.signal_id

        # Add exception info
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        return json.dumps(log_entry, default=str)


class DevFormatter(logging.Formatter):
    """Human-readable formatter for development."""

    def format(self, record: logging.LogRecord) -> str:
        request_id = getattr(record, "request_id", None)
        prefix = f"[{request_id}] " if request_id else ""
        timestamp = datetime.now().strftime("%H:%M:%S")
        return (
            f"{timestamp} {record.levelname:>7} "
            f"{record.name}: {prefix}{record.getMessage()}"
        )


def configure_logging(
    level: Optional[str] = None,
    json_format: Optional[bool] = None,
) -> None:
    """
    Configure application-wide logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR). Default from DSI_LOG_LEVEL env.
        json_format: Use JSON format. Default: True in production, False otherwise.
    """
    log_level = level or os.getenv("DSI_LOG_LEVEL", "INFO")
    env = os.getenv("DSI_ENV", "development")

    if json_format is None:
        json_format = env == "production"

    # Create formatter
    formatter = JSONFormatter() if json_format else DevFormatter()

    # Configure root handler
    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicates
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root.addHandler(handler)

    # Suppress noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if os.getenv("DSI_DEBUG", "false").lower() == "true"
        else logging.WARNING
    )


class RequestLogger:
    """Logger adapter that injects request context."""

    def __init__(self, logger: logging.Logger, request_id: str):
        self._logger = logger
        self._request_id = request_id

    def _log(self, level: int, msg: str, **kwargs):
        extra = {"request_id": self._request_id}
        extra.update(kwargs)
        self._logger.log(level, msg, extra=extra)

    def info(self, msg: str, **kwargs):
        self._log(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs):
        self._log(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs):
        self._log(logging.ERROR, msg, **kwargs)

    def debug(self, msg: str, **kwargs):
        self._log(logging.DEBUG, msg, **kwargs)


def get_request_logger(request_id: str, name: str = "dsi.api") -> RequestLogger:
    """Get a logger that includes the request correlation ID."""
    return RequestLogger(logging.getLogger(name), request_id)
