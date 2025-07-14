"""Rate limiting for Riot API requests."""

from typing import Any

from aiolimiter import AsyncLimiter

from .logging import get_logger


class RateLimiter:
    """Rate limiter for API requests using aiolimiter."""

    def __init__(
        self,
        per_second_limit: tuple[int, int] = (20, 1),
        per_minute_limit: tuple[int, int] = (100, 2),
    ) -> None:
        """
        Initialize rate limiter with Riot API limits.

        Args:
            per_second_limit: (Requests, per second)
            per_minute_limit: (Requests, per minute)
        """
        self._per_second_limit = per_second_limit
        self._per_minute_limit = per_minute_limit
        self._limiter_per_second = AsyncLimiter(*self._per_second_limit)
        self._limiter_per_two_minutes = AsyncLimiter(*self._per_minute_limit)
        self._logger = get_logger()

        self._logger.logger.debug("Rate limiter initialized with aiolimiter.")

    async def async_wait_if_needed(self) -> None:
        """Wait if necessary to comply with rate limits."""
        async with self._limiter_per_second, self._limiter_per_two_minutes:
            self._logger.logger.debug("Rate limit check passed - proceeding with request.")

    def get_status(self) -> dict[str, Any]:
        """
        Get current rate limiter status.

        Note: aiolimiter does not expose current usage or remaining requests directly.
        """
        return {
            "per_second_limit": {
                "requests": self._per_second_limit[0],
                "window_seconds": self._per_second_limit[1],
                "note": "aiolimiter does not expose current usage directly.",
            },
            "per_minute_limit": {
                "requests": self._per_minute_limit[0],
                "window_seconds": self._per_minute_limit[1],
                "note": "aiolimiter does not expose current usage directly.",
            },
        }

    @classmethod
    def create_default(cls) -> "RateLimiter":
        """Create rate limiter with default Riot API limits."""
        return cls()
