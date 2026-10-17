import functools
import os
import re
import time
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging_config import get_logger, request_id_var

logger = get_logger(__name__)

_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def setup_tracing() -> bool:
    """Turn LangSmith tracing on or off from settings. Returns True if enabled."""
    settings = get_settings()

    if settings.langsmith_tracing and not settings.langsmith_api_key:
        logger.warning("LANGSMITH_TRACING is true but LANGSMITH_API_KEY is empty: tracing disabled")
        os.environ["LANGSMITH_TRACING"] = "false"
        return False

    if not settings.langsmith_tracing:
        os.environ["LANGSMITH_TRACING"] = "false"
        logger.info("LangSmith tracing is off")
        return False

    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    if settings.langsmith_endpoint:
        os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint

    logger.info("LangSmith tracing is on (project=%s)", settings.langsmith_project)
    return True


def resolve_request_id(header_value: str | None) -> str:
    """Use the client's X-Request-ID if it is safe, otherwise make a new one."""
    if header_value and _VALID_REQUEST_ID.match(header_value):
        return header_value
    return uuid.uuid4().hex[:12]


async def request_context_middleware(request: Request, call_next):
    """Give each request an ID, log its duration, and catch unexpected errors."""
    request_id = resolve_request_id(request.headers.get("X-Request-ID"))
    token = request_id_var.set(request_id)
    start = time.perf_counter()

    try:
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("Unhandled error on %s %s", request.method, request.url.path)
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "request_id": request_id},
            )

        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "%s %s -> %d (%.0f ms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
    finally:
        request_id_var.reset(token)


def timed_node(name: str):
    """Decorator for graph nodes: log how long each node takes."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(state):
            start = time.perf_counter()
            try:
                result = func(state)
            except Exception:
                logger.error("Node %s failed after %.2fs", name, time.perf_counter() - start)
                raise
            logger.info("Node %s finished in %.2fs", name, time.perf_counter() - start)
            return result

        return wrapper

    return decorator