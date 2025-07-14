"""Tests for rate limiting functionality."""

from unittest.mock import AsyncMock, patch

import pytest

from nexar import RateLimiter


class TestRateLimiter:
    """Test RateLimiter functionality."""

    @pytest.mark.asyncio
    @patch("nexar.rate_limiter.AsyncLimiter")
    async def test_async_wait_if_needed_20_per_sec(self, mock_async_limiter: AsyncMock) -> None:
        """Test async_wait_if_needed for the 20 requests/sec limit."""
        # Configure the mock to return a context manager
        mock_limiter_per_second = AsyncMock()
        mock_limiter_per_minute = AsyncMock()

        mock_async_limiter.side_effect = [mock_limiter_per_second, mock_limiter_per_minute]

        rate_limiter = RateLimiter()

        # The first 20 calls should acquire without blocking
        for _ in range(20):
            await rate_limiter.async_wait_if_needed()

        assert mock_limiter_per_second.__aenter__.call_count == 20
        assert mock_limiter_per_minute.__aenter__.call_count == 20

        # The 21st call should still acquire, but aiolimiter would handle the delay internally
        await rate_limiter.async_wait_if_needed()
        assert mock_limiter_per_second.__aenter__.call_count == 21
        assert mock_limiter_per_minute.__aenter__.call_count == 21

    @pytest.mark.asyncio
    @patch("nexar.rate_limiter.AsyncLimiter")
    async def test_async_wait_if_needed_100_per_2_min(self, mock_async_limiter: AsyncMock) -> None:
        """Test async_wait_if_needed for the 100 requests/2 min limit."""
        # Configure the mock to return a context manager
        mock_limiter_per_second = AsyncMock()
        mock_limiter_per_minute = AsyncMock()

        mock_async_limiter.side_effect = [mock_limiter_per_second, mock_limiter_per_minute]

        rate_limiter = RateLimiter()

        # The first 100 calls should acquire without blocking
        for _ in range(100):
            await rate_limiter.async_wait_if_needed()

        assert mock_limiter_per_second.__aenter__.call_count == 100
        assert mock_limiter_per_minute.__aenter__.call_count == 100

        # The 101st call should still acquire, but aiolimiter would handle the delay internally
        await rate_limiter.async_wait_if_needed()
        assert mock_limiter_per_second.__aenter__.call_count == 101
        assert mock_limiter_per_minute.__aenter__.call_count == 101

    def test_get_status(self) -> None:
        """Test get_status returns the expected structure."""
        rate_limiter = RateLimiter()
        status = rate_limiter.get_status()
        assert "per_second_limit" in status
        assert "per_minute_limit" in status
        assert status["per_second_limit"]["requests"] == 20
        assert status["per_second_limit"]["window_seconds"] == 1
        assert status["per_minute_limit"]["requests"] == 100
        assert status["per_minute_limit"]["window_seconds"] == 2
