"""Tests for custom exceptions."""

import pytest

from nexar.exceptions import ForbiddenError, NotFoundError, RateLimitError, RiotAPIError, UnauthorizedError


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
