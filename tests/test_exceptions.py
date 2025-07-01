"""Tests for custom exceptions."""

from nexar.exceptions import (
    ForbiddenError,
    NexarError,
    NotFoundError,
    RateLimitError,
    RiotAPIError,
    UnauthorizedError,
)


class TestNexarError:
    """Test the base NexarError exception."""

    def test_nexar_error_inheritance(self):
        """Test that NexarError inherits from Exception."""
        error = NexarError("Test error")
        assert isinstance(error, Exception)


class TestRiotAPIError:
    """Test the RiotAPIError exception."""

    def test_riot_api_error_creation(self):
        """Test RiotAPIError creation."""
        error = RiotAPIError(404, "Not found")

        assert error.status_code == 404
        assert error.message == "Not found"
        assert str(error) == "HTTP 404: Not found"

    def test_riot_api_error_inheritance(self):
        """Test that RiotAPIError inherits from NexarError."""
        error = RiotAPIError(500, "Server error")
        assert isinstance(error, NexarError)


class TestSpecificErrors:
    """Test specific error types."""

    def test_rate_limit_error(self):
        """Test RateLimitError."""
        error = RateLimitError(429, "Rate limit exceeded")

        assert isinstance(error, RiotAPIError)
        assert error.status_code == 429

    def test_not_found_error(self):
        """Test NotFoundError."""
        error = NotFoundError(404, "Resource not found")

        assert isinstance(error, RiotAPIError)
        assert error.status_code == 404

    def test_unauthorized_error(self):
        """Test UnauthorizedError."""
        error = UnauthorizedError(401, "Invalid API key")

        assert isinstance(error, RiotAPIError)
        assert error.status_code == 401

    def test_forbidden_error(self):
        """Test ForbiddenError."""
        error = ForbiddenError(403, "Access forbidden")

        assert isinstance(error, RiotAPIError)
        assert error.status_code == 403
