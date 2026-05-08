"""
Middleware — Rate limiter
─────────────────────────
In-memory sliding-window rate limiter applied before handlers.
"""

from __future__ import annotations

import datetime as dt
import logging
from collections import defaultdict

import config

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory per-user rate limiter."""

    def __init__(self) -> None:
        # user_id -> list of timestamps
        self._timestamps: dict[int, list[dt.datetime]] = defaultdict(list)

    def _cleanup(self, user_id: int) -> None:
        cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=1)
        self._timestamps[user_id] = [
            ts for ts in self._timestamps[user_id] if ts > cutoff
        ]

    def is_rate_limited(self, user_id: int) -> bool:
        self._cleanup(user_id)
        return len(self._timestamps[user_id]) >= config.RATE_LIMIT_PER_HOUR

    def record(self, user_id: int) -> None:
        self._timestamps[user_id].append(dt.datetime.now(dt.timezone.utc))

    def seconds_until_next(self, user_id: int) -> int:
        """Seconds until the user can send again (cooldown)."""
        if not self._timestamps[user_id]:
            return 0
        last = self._timestamps[user_id][-1]
        elapsed = (dt.datetime.now(dt.timezone.utc) - last).total_seconds()
        remaining = config.APOLOGY_COOLDOWN_SECONDS - elapsed
        return max(0, int(remaining))


# Singleton
rate_limiter = RateLimiter()
