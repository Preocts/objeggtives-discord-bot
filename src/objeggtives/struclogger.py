"""Structure logging factory and logger for the objeggtives package."""

from __future__ import annotations

import datetime
import json
import logging
import traceback
from typing import Any

# Save the original as we will be replacing it.
_LOG_RECORD_FACTORY = logging.getLogRecordFactory()


class _StringEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> str:
        # Format any datetime objects as ISO 8601 strings.
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%Y-%m-%dT%H:%M:%S%z")

        # Throw everything else to a string and hope for the best.
        else:
            try:
                return super().default(obj)

            except TypeError:
                return str(obj)


def struc_factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
    """Create a LogRecord with a structured message."""
    record = _LOG_RECORD_FACTORY(*args, **kwargs)

    if record.exc_info:
        exc_text = traceback.format_exception(*record.exc_info)

    struc = {
        "level": record.levelname,
        "unixtime": record.created,
        "timestamp": datetime.datetime.fromtimestamp(record.created),
        "thread": record.thread,
        "filename": record.filename,
        "funcname": record.funcName,
        "linenumber": record.lineno,
        "location": f"{record.filename}:{record.funcName}:{record.lineno}",
        "exception": record.exc_info,
        "traceback": exc_text if record.exc_info else None,
        "application": "objeggtives",
        "message": record.getMessage(),
    }
    record.json_formatted = json.dumps(struc, cls=_StringEncoder)

    return record


def init_struclogger() -> None:
    """Initialize the structured logging factory."""
    logging.setLogRecordFactory(struc_factory)


def get_logger(name: str) -> logging.Logger:
    """Create a logger with the structured logging factory."""
    logger = logging.getLogger(name)
    json_formatter = logging.Formatter("%(json_formatted)s")
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(json_formatter)
    logger.addHandler(console_handler)

    return logger
