import logging
import sys
from contextvars import ContextVar

from app.core.config import get_settings

# Holds the ID of the request currently being handled ("-" outside a request).
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    """Attach the current request ID to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


def setup_logging() -> None:
    """Configure logging for the whole application."""
    settings = get_settings()

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(request_id)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.log_level.upper())

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger, e.g. get_logger(__name__)."""
    return logging.getLogger(name)