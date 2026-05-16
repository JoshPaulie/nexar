"""Custom exceptions for the Nexar SDK."""

from collections.abc import Sequence
from typing import Any


class NexarError(Exception):
    """Base exception for all Nexar SDK errors."""


class RiotAPIError(NexarError):
    """Raised when the Riot API returns an error."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"HTTP {status_code}: {message}")


class RateLimitError(RiotAPIError):
    """Raised when rate limit is exceeded."""


class NotFoundError(RiotAPIError):
    """Raised when requested resource is not found."""


class UnauthorizedError(RiotAPIError):
    """Raised when API key is invalid or missing."""


class ForbiddenError(RiotAPIError):
    """Raised when access is forbidden."""


class BatchError(NexarError):
    """Raised when one or more operations in a batch fail."""

    def __init__(
        self,
        errors: Sequence[tuple[int | str, BaseException]],
        successful_results: list[Any] | None = None,
        message: str | None = None,
    ) -> None:
        self.errors: list[tuple[str, BaseException]] = [
            (label if isinstance(label, str) else f"item[{label}]", exc) for label, exc in errors
        ]
        self.successful_results = successful_results or []
        msg = message or self._format_errors()
        super().__init__(msg)

    def _format_errors(self) -> str:
        details = "; ".join(f"{idx}: {exc}" for idx, exc in self.errors)
        return f"{len(self.errors)} operation(s) failed: {details}"
