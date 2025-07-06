"""Rate limiting for Riot API requests."""

import asyncio
import time
from collections import deque
from dataclasses import dataclass
from typing import Any

from .logging import get_logger


@dataclass
class RateLimit:
    """Rate limit configuration."""

    requests: int
    """Maximum number of requests allowed."""

    window_seconds: int
    """Time window in seconds."""


class RateLimiter:
    """Rate limiter for API requests with multiple time windows."""

    def __init__(self, rate_limits: list[RateLimit]) -> None:
        """
        Initialize rate limiter with multiple rate limits.

        Args:
            rate_limits: List of rate limit configurations to enforce

        """
        self.rate_limits = rate_limits
        # Track request timestamps for each rate limit
        self._request_queues: list[deque[float]] = [deque() for _ in rate_limits]
        self._logger = get_logger()

        # Log rate limiter initialization
        self._logger.logger.debug(
            "Rate limiter initialized with %d limits:",
            len(rate_limits),
        )
        for i, limit in enumerate(rate_limits):
            self._logger.logger.debug(
                "  Limit %d: %d requests per %ds",
                i + 1,
                limit.requests,
                limit.window_seconds,
            )

    def wait_if_needed(self) -> None:
        """Wait if necessary to comply with rate limits."""
        current_time = time.time()
        max_wait_time = 0.0
        limiting_constraint = None

        for i, (rate_limit, request_queue) in enumerate(
            zip(self.rate_limits, self._request_queues, strict=False),
        ):
            # Remove old requests outside the time window
            cutoff_time = current_time - rate_limit.window_seconds
            removed_count = 0
            while request_queue and request_queue[0] <= cutoff_time:
                request_queue.popleft()
                removed_count += 1

            if removed_count > 0:
                self._logger.logger.debug(
                    "Cleaned up %d expired requests from limit %d",
                    removed_count,
                    i + 1,
                )

            # Check current status
            current_usage = len(request_queue)
            remaining = rate_limit.requests - current_usage
            self._logger.logger.debug(
                "Limit %d: %d/%d used, %d remaining",
                i + 1,
                current_usage,
                rate_limit.requests,
                remaining,
            )

            # Check if we need to wait
            if len(request_queue) >= rate_limit.requests:
                # Calculate wait time until oldest request expires
                oldest_request = request_queue[0]
                wait_time = (oldest_request + rate_limit.window_seconds) - current_time
                if wait_time > max_wait_time:
                    max_wait_time = wait_time
                    limiting_constraint = f"Limit {i + 1} ({rate_limit.requests} req/{rate_limit.window_seconds}s)"

        if max_wait_time > 0:
            self._logger.logger.info(
                "Rate limit hit! %s - waiting %.2f seconds",
                limiting_constraint,
                max_wait_time,
            )
            time.sleep(max_wait_time)

    async def async_wait_if_needed(self) -> None:
        """Async version of wait_if_needed."""
        current_time = time.time()
        max_wait_time = 0.0
        limiting_constraint = None

        for i, (rate_limit, request_queue) in enumerate(
            zip(self.rate_limits, self._request_queues, strict=False),
        ):
            # Remove old requests outside the time window
            cutoff_time = current_time - rate_limit.window_seconds
            removed_count = 0
            while request_queue and request_queue[0] <= cutoff_time:
                request_queue.popleft()
                removed_count += 1

            if removed_count > 0:
                self._logger.logger.debug(
                    "Cleaned up %d expired requests from limit %d",
                    removed_count,
                    i + 1,
                )

            # Check current status
            current_usage = len(request_queue)
            remaining = rate_limit.requests - current_usage
            self._logger.logger.debug(
                "Limit %d: %d/%d used, %d remaining",
                i + 1,
                current_usage,
                rate_limit.requests,
                remaining,
            )

            # Check if we need to wait
            if len(request_queue) >= rate_limit.requests:
                # Calculate wait time until oldest request expires
                oldest_request = request_queue[0]
                wait_time = (oldest_request + rate_limit.window_seconds) - current_time
                if wait_time > max_wait_time:
                    max_wait_time = wait_time
                    limiting_constraint = f"Limit {i + 1} ({rate_limit.requests} req/{rate_limit.window_seconds}s)"

        if max_wait_time > 0:
            self._logger.logger.info(
                "Rate limit hit! %s - waiting %.2f seconds",
                limiting_constraint,
                max_wait_time,
            )
            await asyncio.sleep(max_wait_time)
            self._logger.logger.info(
                "Rate limit wait complete - proceeding with request",
            )
        else:
            self._logger.logger.debug(
                "No rate limiting required - proceeding immediately",
            )

    def record_request(self) -> None:
        """Record a new request timestamp."""
        current_time = time.time()

        # Add current request to all queues
        for _i, request_queue in enumerate(self._request_queues):
            request_queue.append(current_time)

        self._logger.logger.debug("Request recorded at %.3f", current_time)

    def get_status(self) -> dict[str, Any]:
        """
        Get current rate limiter status.

        Returns:
            Dictionary with current usage for each rate limit

        """
        current_time = time.time()
        status = {}

        for i, (rate_limit, request_queue) in enumerate(
            zip(self.rate_limits, self._request_queues, strict=False),
        ):
            # Remove old requests outside the time window
            cutoff_time = current_time - rate_limit.window_seconds
            while request_queue and request_queue[0] <= cutoff_time:
                request_queue.popleft()

            remaining = rate_limit.requests - len(request_queue)
            status[f"limit_{i + 1}"] = {
                "requests": rate_limit.requests,
                "window_seconds": rate_limit.window_seconds,
                "current_usage": len(request_queue),
                "remaining": max(0, remaining),
                "reset_in_seconds": (
                    (request_queue[0] + rate_limit.window_seconds) - current_time if request_queue else 0
                ),
            }

        return status

    @classmethod
    def create_default(cls) -> "RateLimiter":
        """
        Create rate limiter with default Riot API limits.

        Returns:
            RateLimiter configured with 20 req/1s and 100 req/2min

        """
        return cls(
            [
                RateLimit(requests=20, window_seconds=1),
                RateLimit(requests=100, window_seconds=120),  # 2 minutes
            ],
        )
