"""Tests for rate limiting functionality."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from nexar import RateLimiter


class TestRateLimiter:
    """Test RateLimiter functionality."""

    @pytest.mark.asyncio
    @patch("nexar.rate_limiter.AsyncLimiter")
    async def test_async_wait_if_needed_20_per_sec(self, MockAsyncLimiter: AsyncMock) -> None:
        """Test async_wait_if_needed for the 20 requests/sec limit."""
        # Configure the mock to return a context manager
        mock_limiter_20_1s = AsyncMock()
        mock_limiter_100_120s = AsyncMock()

        MockAsyncLimiter.side_effect = [mock_limiter_20_1s, mock_limiter_100_120s]

        rate_limiter = RateLimiter()

        # The first 20 calls should acquire without blocking
        for _ in range(20):
            await rate_limiter.async_wait_if_needed()

        assert mock_limiter_20_1s.__aenter__.call_count == 20
        assert mock_limiter_100_120s.__aenter__.call_count == 20

        # The 21st call should still acquire, but aiolimiter would handle the delay internally
        await rate_limiter.async_wait_if_needed()
        assert mock_limiter_20_1s.__aenter__.call_count == 21
        assert mock_limiter_100_120s.__aenter__.call_count == 21

    @pytest.mark.asyncio
    @patch("nexar.rate_limiter.AsyncLimiter")
    async def test_async_wait_if_needed_100_per_2min(self, MockAsyncLimiter: AsyncMock) -> None:
        """Test async_wait_if_needed for the 100 requests/2min limit."""
        # Configure the mock to return a context manager
        mock_limiter_20_1s = AsyncMock()
        mock_limiter_100_120s = AsyncMock()

        MockAsyncLimiter.side_effect = [mock_limiter_20_1s, mock_limiter_100_120s]

        rate_limiter = RateLimiter()

        # Make 100 calls, which should acquire without blocking
        for _ in range(100):
            await rate_limiter.async_wait_if_needed()

        assert mock_limiter_20_1s.__aenter__.call_count == 100
        assert mock_limiter_100_120s.__aenter__.call_count == 100

        # The 101st call should still acquire, but aiolimiter would handle the delay internally
        await rate_limiter.async_wait_if_needed()
        assert mock_limiter_20_1s.__aenter__.call_count == 101
        assert mock_limiter_100_120s.__aenter__.call_count == 101

    def test_get_status(self) -> None:
        """Test get_status returns the expected structure."""
        rate_limiter = RateLimiter()
        status = rate_limiter.get_status()
        assert "limit_20_1s" in status
        assert "limit_100_120s" in status
        assert status["limit_20_1s"]["requests"] == 20
        assert status["limit_100_120s"]["requests"] == 100
