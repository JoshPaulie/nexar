"""Custom exceptions for the Nexar SDK."""

import asyncio
from collections.abc import Awaitable, Callable, Sequence
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


async def gather_partitioned[K, T](
    keys: Sequence[K],
    fetch: Callable[[K], Awaitable[T]],
) -> tuple[list[T], list[tuple[K, BaseException]]]:
    """Run one awaitable per key and partition the outcomes.

    This is the batch path behind ``NexarClient.get_players`` and
    ``Player.get_matches``: successes keep ``gather``'s input order, failures
    pair with their key for ``BatchError``. The partition checks
    ``BaseException``, matching ``BatchError``'s declared error type —
    ``gather(return_exceptions=True)`` captures ``BaseException`` instances
    as results (``KeyboardInterrupt`` and ``SystemExit`` additionally
    re-raise into the caller, so only quieter ``BaseException`` subclasses
    reach the partition). Results align with ``keys`` by construction,
    hence ``strict``.
    """
    results = await asyncio.gather(*(fetch(k) for k in keys), return_exceptions=True)
    successes: list[T] = []
    errors: list[tuple[K, BaseException]] = []
    for key, result in zip(keys, results, strict=True):
        if isinstance(result, BaseException):
            errors.append((key, result))
        else:
            successes.append(result)
    return successes, errors
