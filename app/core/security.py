import secrets

from fastapi import Header, HTTPException

from app.core.config import get_settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """FastAPI dependency: require a matching X-API-Key header.

    If API_KEY is not configured, authentication is disabled (local development).
    """
    expected = get_settings().api_key
    if not expected:
        return

    provided = x_api_key or ""
    if not secrets.compare_digest(provided.encode("utf-8"), expected.encode("utf-8")):
        logger.warning("Rejected request with a missing or wrong API key")
        raise HTTPException(status_code=401, detail="Invalid or missing API key")