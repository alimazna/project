"""Minimal in-memory sliding-window rate limiter.

Single-process only (fine for the SQLite/single-worker dev deployment).
Swap for a Redis-backed limiter when running multi-worker.
"""

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

_windows: dict[tuple, deque[float]] = defaultdict(deque)
_window_start: dict[tuple, float] = {}


def rate_limit(limit: int, window_seconds: int, scope: str = "auth"):
    """Return a FastAPI dependency allowing ``limit`` calls / window per IP."""

    def dep(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        key = (scope, client_ip)
        now = time.monotonic()
        start = _window_start.get(key, now)
        if now - start >= window_seconds:
            start = now
            _window_start[key] = start
            _windows[key].clear()
        bucket = _windows[key]
        while bucket and now - bucket[0] >= window_seconds:
            bucket.popleft()
        bucket.append(now)
        if len(bucket) > limit:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "Too many requests, slow down",
                headers={"Retry-After": str(window_seconds)},
            )

    return dep


def reset_rate_limits() -> None:
    """Clear limiter state (used between tests)."""
    _windows.clear()
    _window_start.clear()
