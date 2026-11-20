"""Tests for custom exceptions."""

import pytest

from nexar.exceptions import (
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    RiotAPIError,
    UnauthorizedError,
    gather_partitioned,
)


def test_riot_api_error_creation() -> None:
    """The user-visible message format is pinned."""
    error = RiotAPIError(404, "Not found")

    assert error.status_code == 404
    assert error.message == "Not found"
    assert str(error) == "HTTP 404: Not found"


@pytest.mark.parametrize(
    ("error_class", "status"),
    [
        (RateLimitError, 429),
        (NotFoundError, 404),
        (UnauthorizedError, 401),
        (ForbiddenError, 403),
    ],
)
def test_status_errors_extend_riot_api_error(error_class: type, status: int) -> None:
    """Each HTTP-status subclass is a RiotAPIError carrying its status."""
    error = error_class(status, "boom")

    assert isinstance(error, RiotAPIError)
    assert error.status_code == status


class BatchAbort(BaseException):
    """A BaseException that is not KeyboardInterrupt/SystemExit.

    Only those two re-raise into the caller through the task machinery; a
    quieter BaseException subclass stays captured by
    gather(return_exceptions=True), which is exactly the case the partition
    must route to errors.
    """


@pytest.mark.asyncio
async def test_gather_partitioned_routes_base_exceptions_to_errors() -> None:
    """Route captured BaseException results to errors, never successes.

    The narrow Exception check of the old get_players variant would have
    routed a captured BaseException subclass into the successes.
    """

    async def fetch(key: str) -> int:
        if key == "aborted":
            raise BatchAbort
        return len(key)

    successes, errors = await gather_partitioned(["ok", "aborted", "abc"], fetch)

    assert successes == [2, 3]
    assert [key for key, _ in errors] == ["aborted"]
    assert isinstance(errors[0][1], BatchAbort)
