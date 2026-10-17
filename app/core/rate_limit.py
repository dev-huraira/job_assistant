import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request

from app.core.config import get_settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class SlidingWindowRateLimiter:
    """Allow at most max_requests per key within a sliding time window."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]

            while hits and now - hits[0] > self.window_seconds:
                hits.popleft()

            if len(hits) >= self.max_requests:
                retry_after = int(self.window_seconds - (now - hits[0])) + 1
                logger.warning("Rate limit exceeded for %s", key)
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many requests. Try again in {retry_after} seconds.",
                    headers={"Retry-After": str(retry_after)},
                )

            hits.append(now)


_settings = get_settings()
limiter = SlidingWindowRateLimiter(
    max_requests=_settings.rate_limit_max_requests,
    window_seconds=_settings.rate_limit_window_seconds,
)


def rate_limit_applications(request: Request) -> None:
    """FastAPI dependency: rate-limit by the caller's IP address."""
    client_ip = request.client.host if request.client else "unknown"
    limiter.check(client_ip)