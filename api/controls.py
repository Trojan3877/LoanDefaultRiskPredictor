"""Small in-process serving controls; distributed limits belong at the gateway."""

from __future__ import annotations

import hmac
import time
from collections import defaultdict, deque
from threading import Lock


class SlidingWindowRateLimiter:
    def __init__(self, limit: int, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            events = self._events[key]
            while events and now - events[0] >= self.window_seconds:
                events.popleft()
            if len(events) >= self.limit:
                return False
            events.append(now)
            return True


def valid_api_key(expected: str | None, supplied: str | None) -> bool:
    return expected is None or (supplied is not None and hmac.compare_digest(expected, supplied))
