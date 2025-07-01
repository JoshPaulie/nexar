"""Custom exceptions for the Nexar SDK."""


class NexarError(Exception):
    """Base exception for all Nexar SDK errors."""

    pass


class RiotAPIError(NexarError):
    """Raised when the Riot API returns an error."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"HTTP {status_code}: {message}")


class RateLimitError(RiotAPIError):
    """Raised when rate limit is exceeded."""

    pass


class NotFoundError(RiotAPIError):
    """Raised when requested resource is not found."""

    pass


class UnauthorizedError(RiotAPIError):
    """Raised when API key is invalid or missing."""

    pass


class ForbiddenError(RiotAPIError):
    """Raised when access is forbidden."""

    pass
