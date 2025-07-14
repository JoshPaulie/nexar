"""Rate limiting for Riot API requests."""

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
            per_second_limit: Tuple of (max_requests, seconds). E.g., (20, 1) for max 20 requests per 1 second.
            per_minute_limit: Tuple of (max_requests, minutes). E.g., (100, 2) for max 100 requests per 2 minutes.

        """
        self._per_second_limit = per_second_limit
        self._per_minute_limit = per_minute_limit
        self._limiter_per_second = AsyncLimiter(*self._per_second_limit)
        self._limiter_per_two_minutes = AsyncLimiter(
            self._per_minute_limit[0], self._per_minute_limit[1] * 60
        )
        self._logger = get_logger()

        self._logger.logger.debug("Rate limiter initialized with aiolimiter.")

    async def async_wait_if_needed(self) -> None:
        """Wait if necessary to comply with rate limits."""
        async with self._limiter_per_second, self._limiter_per_two_minutes:
            self._logger.logger.debug("Rate limit check passed - proceeding with request.")

    @classmethod
    def create_default(cls) -> "RateLimiter":
        """Create rate limiter with default Riot API limits."""
        return cls()
