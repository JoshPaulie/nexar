"""Rate limiting for Riot API requests."""

from typing import Any

from aiolimiter import AsyncLimiter

from .logging import get_logger


class RateLimiter:
    """Rate limiter for API requests using aiolimiter."""

    def __init__(self) -> None:
        """
        Initialize rate limiter with Riot API limits.

        Riot API has 2 rate limits: 20 requests per second and 100 requests per 2 minutes.
        """
        self._limiter_20_1s = AsyncLimiter(20, 1)
        self._limiter_100_120s = AsyncLimiter(100, 120)
        self._logger = get_logger()

        self._logger.logger.debug("Rate limiter initialized with aiolimiter.")

    async def async_wait_if_needed(self) -> None:
        """Wait if necessary to comply with rate limits."""
        async with self._limiter_20_1s, self._limiter_100_120s:
            self._logger.logger.debug("Rate limit check passed - proceeding with request.")

    def get_status(self) -> dict[str, Any]:
        """
        Get current rate limiter status.

        Note: aiolimiter does not expose current usage or remaining requests directly.
        """
        return {
            "limit_20_1s": {
                "requests": 20,
                "window_seconds": 1,
                "note": "aiolimiter does not expose current usage directly.",
            },
            "limit_100_120s": {
                "requests": 100,
                "window_seconds": 120,
                "note": "aiolimiter does not expose current usage directly.",
            },
        }

    @classmethod
    def create_default(cls) -> "RateLimiter":
        """Create rate limiter with default Riot API limits."""
        return cls()
