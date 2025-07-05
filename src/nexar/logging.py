"""Logging configuration for the Nexar SDK."""

import logging
from typing import Any


class NexarLogger:
    """Centralized logging for the Nexar SDK."""

    def __init__(self, name: str = "nexar") -> None:
        """
        Initialize the logger.

        Args:
            name: Logger name

        """
        self.logger = logging.getLogger(name)
        self._call_stats = {"total_calls": 0, "cache_hits": 0, "fresh_calls": 0}

    def configure(self, level: int = logging.INFO) -> None:
        """
        Configure the logger with a console handler.

        Args:
            level: Logging level

        """
        # Remove any existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Create console handler
        handler = logging.StreamHandler()

        # Create formatter
        formatter = logging.Formatter("[%(name)s] %(message)s")
        handler.setFormatter(formatter)

        # Add handler to logger
        self.logger.addHandler(handler)
        self.logger.setLevel(level)

        # Prevent propagation to root logger
        self.logger.propagate = False

    def log_api_call_start(
        self,
        call_number: int,
        endpoint: str,
        region: str,
        params: dict[str, Any] | None = None,
    ) -> None:
        """
        Log the start of an API call.

        Args:
            call_number: Sequential API call number
            endpoint: API endpoint path
            region: Region for the call
            params: Optional query parameters

        """
        self._call_stats["total_calls"] += 1
        self.logger.info(
            "API Call #%d: %s (region: %s)",
            call_number,
            endpoint,
            region,
        )
        if params:
            self.logger.debug("  Params: %s", params)

    def log_api_call_success(self, status_code: int, *, from_cache: bool) -> None:
        """
        Log successful API call completion.

        Args:
            status_code: HTTP status code
            from_cache: Whether response came from cache

        """
        if from_cache:
            self._call_stats["cache_hits"] += 1
            cache_status = "from cache"
        else:
            self._call_stats["fresh_calls"] += 1
            cache_status = "fresh"

        self.logger.info(
            "  \u2713 Success (Status: %d, %s)",
            status_code,
            cache_status,
        )

    def log_api_call_error(self, error: Exception) -> None:
        """
        Log API call error.

        Args:
            error: The error that occurred

        """
        self.logger.error("  \u2717 Error: %s", error)

    def log_cache_setup(
        self,
        cache_name: str,
        backend: str,
        *,
        has_cache: bool,
        cache_type: type | None = None,
    ) -> None:
        """
        Log cache setup information.

        Args:
            cache_name: Name of the cache
            backend: Cache backend type
            has_cache: Whether session has cache
            cache_type: Type of cache backend

        """
        self.logger.info("Caching enabled: %s.%s", cache_name, backend)
        self.logger.debug("Session has cache: %s", has_cache)
        if cache_type:
            self.logger.debug("Cache backend: %s", cache_type)

    def log_cache_config(self, expire_after: int, *, has_url_expiration: bool) -> None:
        """
        Log cache configuration details.

        Args:
            expire_after: Default expiration time
            has_url_expiration: Whether per-URL expiration is configured

        """
        self.logger.debug("Default expire_after: %d", expire_after)
        self.logger.debug("Per-URL expiration configured: %s", has_url_expiration)

    def log_cache_cleared(self) -> None:
        """Log cache clearing."""
        self.logger.info("Cache cleared")

    def log_stats_summary(self) -> None:
        """Log API call statistics summary."""
        total = self._call_stats["total_calls"]
        cache_hits = self._call_stats["cache_hits"]
        fresh = self._call_stats["fresh_calls"]

        if total > 0:
            cache_hit_rate = (cache_hits / total) * 100
            self.logger.info(
                "API Stats: %d calls total, %d fresh, %d cached (%.1f%% cache hit rate)",
                total,
                fresh,
                cache_hits,
                cache_hit_rate,
            )
        else:
            self.logger.info(
                "No API calls made yet. Enable logging to see detailed call information.",
            )

    def get_stats(self) -> dict[str, int]:
        """
        Get current API call statistics.

        Returns:
            Dictionary with call statistics

        """
        return self._call_stats.copy()

    def reset_stats(self) -> None:
        """Reset API call statistics."""
        self._call_stats = {"total_calls": 0, "cache_hits": 0, "fresh_calls": 0}


# Global logger instance
_nexar_logger = NexarLogger()


def get_logger() -> NexarLogger:
    """
    Get the global Nexar logger instance.

    Returns:
        The global logger instance

    """
    return _nexar_logger


def configure_logging(level: int = logging.INFO) -> None:
    """
    Configure Nexar logging.

    Args:
        level: Logging level (default: INFO)

    """
    _nexar_logger.configure(level)
