from __future__ import annotations

import json
import logging
import os
from typing import Final


_LOG_CONFIGURED: Final[bool] = False


def _configure_root_logger() -> None:
    global _LOG_CONFIGURED
    if getattr(logging.getLogger(), "handlers", []):
        return

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    log_format = os.getenv("LOG_FORMAT", "plain").lower()
    service_name = os.getenv("SERVICE_NAME", "")

    handler = logging.StreamHandler()

    if log_format == "json":
        class JsonFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
                payload = {
                    "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                }
                if service_name:
                    payload["service"] = service_name
                return json.dumps(payload, ensure_ascii=False)

        formatter: logging.Formatter = JsonFormatter()
    else:
        pattern = "%(asctime)s [%(levelname)s]"
        if service_name:
            pattern += f" [{service_name}]"
        pattern += " %(name)s: %(message)s"
        formatter = logging.Formatter(pattern, "%Y-%m-%d %H:%M:%S")

    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:


    _configure_root_logger()
    return logging.getLogger(name)
