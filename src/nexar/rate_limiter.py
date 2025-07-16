"""Rate limiting for Riot API requests."""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from aiolimiter import AsyncLimiter

from .logging import get_logger


class RateLimiter:
    """
    Rate limiter for API requests using aiolimiter + minimum intreval.

    Abiding by the strictest rate limiter is recommended by Riot's "Third Party Developer" discord.
    Particularly Botty McBotface.
    """

    def __init__(
        self,
        per_second_limit: tuple[int, int] = (20, 1),
        per_minute_limit: tuple[int, int] = (100, 2),
    ) -> None:
        """
        Initialize rate limiter with Riot API limits.

        Args:
            per_second_limit: Tuple of (max_requests, seconds). E.g., (20, 1) for max 20 requests per 1 second.
            per_minute_limit: Tuple of (max_requests, minutes). E.g., (100, 2) for max 100 requests per 2 minutes.

        """
        self._per_second_limit = per_second_limit
        self._per_minute_limit = per_minute_limit
        self._limiter_per_second = AsyncLimiter(*self._per_second_limit)
        self._limiter_per_minute = AsyncLimiter(
            self._per_minute_limit[0],
            self._per_minute_limit[1] * 60,
        )
        # Add a minimum interval between requests, set to the slowest of the two windows
        per_second_interval = self._per_second_limit[1] / self._per_second_limit[0]
        per_minute_interval = (self._per_minute_limit[1] * 60) / self._per_minute_limit[0]
        self._min_interval = max(per_second_interval, per_minute_interval)
        self._last_request = 0.0
        self._logger = get_logger()
        self._logger.logger.debug(
            "Rate limiter initialized with aiolimiter and min interval pacing. Min interval: %.3fs",
            self._min_interval,
        )

    @asynccontextmanager
    async def combined_limiters(self) -> AsyncGenerator[None]:
        """
        Acquire both per-second and per-2-min limiters for a single API call.

        Also enforces a minimum interval between requests (lowest of the two windows).
        """
        async with self._limiter_per_second, self._limiter_per_minute:
            import time

            now = time.monotonic()
            elapsed = now - self._last_request
            if elapsed < self._min_interval:
                await asyncio.sleep(self._min_interval - elapsed)
            self._last_request = time.monotonic()
            yield

    async def async_wait_if_needed(self) -> None:
        """Wait if necessary to comply with rate limits and pacing."""
        async with self.combined_limiters():
            self._logger.logger.debug("Rate limit check passed - proceeding with request.")

    @classmethod
    def create_default(cls) -> "RateLimiter":
        """Create rate limiter with default Riot API limits."""
        return cls()
