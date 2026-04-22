"""
Structured logging configuration
"""
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pythonjsonlogger import jsonlogger
from pathlib import Path

from ..config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)

        # Add timestamp in ISO format
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'

        # Add log level
        log_record['level'] = record.levelname

        # Add logger name
        log_record['logger'] = record.name

        # Add location information
        log_record['location'] = {
            'filename': record.filename,
            'lineno': record.lineno,
            'funcName': record.funcName,
        }

        # Add request ID if present
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id

        # Add user ID if present
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id


def setup_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """
    Setup structured logging for the application

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Output format (json, text)
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Set formatter based on format type
    if log_format == "json":
        formatter = CustomJsonFormatter(
            fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%SZ'
        )
    else:
        formatter = logging.Formatter(
            fmt='%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S%z'
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Setup file handler if log directory is configured
    log_dir = getattr(settings, 'LOG_DIR', None)
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        # Rotating file handler
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_path / "app.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
        )
        file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Set third-party logger levels
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(name)


class RequestContextFilter(logging.Filter):
    """Filter to add request context to log records"""

    def __init__(self, request_id: str, user_id: Optional[str] = None):
        super().__init__()
        self.request_id = request_id
        self.user_id = user_id

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = self.request_id
        if self.user_id:
            record.user_id = self.user_id
        return True
