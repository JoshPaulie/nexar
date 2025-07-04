"""Rate limiting for Riot API requests."""

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
        """Initialize rate limiter with multiple rate limits.

        Args:
            rate_limits: List of rate limit configurations to enforce
        """
        self.rate_limits = rate_limits
        # Track request timestamps for each rate limit
        self._request_queues: list[deque[float]] = [deque() for _ in rate_limits]
        self._logger = get_logger()

        # Log rate limiter initialization
        self._logger.logger.debug(
            f"Rate limiter initialized with {len(rate_limits)} limits:"
        )
        for i, limit in enumerate(rate_limits):
            self._logger.logger.debug(
                f"  Limit {i + 1}: {limit.requests} requests per {limit.window_seconds}s"
            )

    def wait_if_needed(self) -> None:
        """Wait if necessary to comply with rate limits."""
        current_time = time.time()
        max_wait_time = 0.0
        limiting_constraint = None

        for i, (rate_limit, request_queue) in enumerate(
            zip(self.rate_limits, self._request_queues)
        ):
            # Remove old requests outside the time window
            cutoff_time = current_time - rate_limit.window_seconds
            removed_count = 0
            while request_queue and request_queue[0] <= cutoff_time:
                request_queue.popleft()
                removed_count += 1

            if removed_count > 0:
                self._logger.logger.debug(
                    f"Cleaned up {removed_count} expired requests from limit {i + 1}"
                )

            # Check current status
            current_usage = len(request_queue)
            remaining = rate_limit.requests - current_usage
            self._logger.logger.debug(
                f"Limit {i + 1}: {current_usage}/{rate_limit.requests} used, {remaining} remaining"
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
                f"Rate limit hit! {limiting_constraint} - waiting {max_wait_time:.2f} seconds"
            )
            time.sleep(max_wait_time)
            self._logger.logger.info(
                "Rate limit wait complete - proceeding with request"
            )
        else:
            self._logger.logger.debug(
                "No rate limiting required - proceeding immediately"
            )

    def record_request(self) -> None:
        """Record a new request timestamp."""
        current_time = time.time()

        # Add current request to all queues
        for i, request_queue in enumerate(self._request_queues):
            request_queue.append(current_time)

        self._logger.logger.debug(f"Request recorded at {current_time:.3f}")

    def get_status(self) -> dict[str, Any]:
        """Get current rate limiter status.

        Returns:
            Dictionary with current usage for each rate limit
        """
        current_time = time.time()
        status = {}

        for i, (rate_limit, request_queue) in enumerate(
            zip(self.rate_limits, self._request_queues)
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
                    (request_queue[0] + rate_limit.window_seconds) - current_time
                    if request_queue
                    else 0
                ),
            }

        return status

    @classmethod
    def create_default(cls) -> "RateLimiter":
        """Create rate limiter with default Riot API limits.

        Returns:
            RateLimiter configured with 20 req/1s and 100 req/2min
        """
        return cls(
            [
                RateLimit(requests=20, window_seconds=1),
                RateLimit(requests=100, window_seconds=120),  # 2 minutes
            ]
        )
