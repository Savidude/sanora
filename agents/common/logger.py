"""Shared JSON logging configuration for all agents."""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any


class JsonFormatter(logging.Formatter):
    """Format log records as one structured JSON object per line."""

    _STANDARD_FIELDS = set(logging.LogRecord(None, 0, "", 0, "", (), None).__dict__)

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        extra = {
            key: value
            for key, value in record.__dict__.items()
            if key not in self._STANDARD_FIELDS and not key.startswith("_")
        }
        if extra:
            payload["context"] = extra

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Configure the agents' root logger once.

    The log level can be controlled with ``AGENTS_LOG_LEVEL`` and defaults to
    ``INFO``. Logs are written to stderr so stdout remains suitable for output
    consumed by callers.
    """

    root_logger = logging.getLogger()
    if any(
        isinstance(handler.formatter, JsonFormatter)
        for handler in root_logger.handlers
    ):
        return

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())

    root_logger.setLevel(os.getenv("AGENTS_LOG_LEVEL", "INFO").upper())
    root_logger.addHandler(handler)


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a configured logger for an agent module."""

    configure_logging()
    return logging.getLogger(name or "agents")
