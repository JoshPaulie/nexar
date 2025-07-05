"""Tests for rate limiting functionality."""

import time
from unittest.mock import patch

from nexar import RateLimit, RateLimiter


class TestRateLimit:
    """Test RateLimit dataclass."""

    def test_rate_limit_creation(self):
        """Test RateLimit can be created with correct attributes."""
        rate_limit = RateLimit(requests=10, window_seconds=60)
        assert rate_limit.requests == 10
        assert rate_limit.window_seconds == 60


class TestRateLimiter:
    """Test RateLimiter functionality."""

    def test_single_rate_limit(self):
        """Test rate limiter with a single rate limit."""
        rate_limiter = RateLimiter([RateLimit(requests=2, window_seconds=1)])

        # First two requests should not block
        rate_limiter.wait_if_needed()
        rate_limiter.record_request()

        rate_limiter.wait_if_needed()
        rate_limiter.record_request()

        # Third request should require waiting
        start_time = time.time()
        rate_limiter.wait_if_needed()
        end_time = time.time()

        # Should have waited approximately 1 second
        assert end_time - start_time >= 0.9  # Allow some tolerance

    def test_multiple_rate_limits(self):
        """Test rate limiter with multiple rate limits."""
        rate_limiter = RateLimiter(
            [
                RateLimit(requests=2, window_seconds=1),
                RateLimit(requests=3, window_seconds=2),
            ],
        )

        # Make 2 requests quickly
        for _ in range(2):
            rate_limiter.wait_if_needed()
            rate_limiter.record_request()

        # Third request should wait due to first rate limit
        start_time = time.time()
        rate_limiter.wait_if_needed()
        end_time = time.time()

        assert end_time - start_time >= 0.9

    def test_default_rate_limiter(self):
        """Test default rate limiter configuration."""
        rate_limiter = RateLimiter.create_default()

        assert len(rate_limiter.rate_limits) == 2
        assert rate_limiter.rate_limits[0].requests == 20
        assert rate_limiter.rate_limits[0].window_seconds == 1
        assert rate_limiter.rate_limits[1].requests == 100
        assert rate_limiter.rate_limits[1].window_seconds == 120

    def test_get_status(self):
        """Test rate limiter status reporting."""
        rate_limiter = RateLimiter([RateLimit(requests=5, window_seconds=10)])

        # Make some requests
        for _ in range(3):
            rate_limiter.record_request()

        status = rate_limiter.get_status()

        assert "limit_1" in status
        assert status["limit_1"]["requests"] == 5
        assert status["limit_1"]["window_seconds"] == 10
        assert status["limit_1"]["current_usage"] == 3
        assert status["limit_1"]["remaining"] == 2

    def test_status_with_expired_requests(self):
        """Test that expired requests are properly cleaned up in status."""
        rate_limiter = RateLimiter([RateLimit(requests=5, window_seconds=1)])

        # Record a request
        rate_limiter.record_request()

        # Wait for it to expire
        time.sleep(1.1)

        status = rate_limiter.get_status()

        # Should show no current usage since request expired
        assert status["limit_1"]["current_usage"] == 0
        assert status["limit_1"]["remaining"] == 5

    def test_no_wait_when_under_limit(self):
        """Test that no waiting occurs when under rate limits."""
        rate_limiter = RateLimiter([RateLimit(requests=10, window_seconds=1)])

        # Should not wait when under limit
        start_time = time.time()
        rate_limiter.wait_if_needed()
        end_time = time.time()

        # Should be essentially instantaneous
        assert end_time - start_time < 0.1

    @patch("time.sleep")
    def test_wait_calculation(self, mock_sleep):
        """Test that wait time is calculated correctly."""
        rate_limiter = RateLimiter([RateLimit(requests=1, window_seconds=2)])

        # Record a request
        rate_limiter.record_request()

        # Next request should wait
        rate_limiter.wait_if_needed()

        # Should have called sleep with approximately 2 seconds
        mock_sleep.assert_called_once()
        call_args = mock_sleep.call_args[0]
        assert 1.9 <= call_args[0] <= 2.1  # Allow some tolerance

    def test_logging_output(self, caplog):
        """Test that rate limiter produces appropriate log messages."""
        import logging

        # Configure logging to capture debug messages
        caplog.set_level(logging.DEBUG, logger="nexar")

        # Create rate limiter
        rate_limiter = RateLimiter([RateLimit(requests=1, window_seconds=1)])

        # Check initialization logging
        assert "Rate limiter initialized with 1 limits" in caplog.text
        assert "Limit 1: 1 requests per 1s" in caplog.text

        # Clear previous logs
        caplog.clear()

        # Test normal operation (should be debug level)
        rate_limiter.wait_if_needed()
        rate_limiter.record_request()

        assert "used, 1 remaining" in caplog.text
        assert "No rate limiting required" in caplog.text
        assert "Request recorded at" in caplog.text

        # Clear logs
        caplog.clear()

        # Test rate limit hit (should be info level)
        with caplog.at_level(logging.INFO, logger="nexar"):
            rate_limiter.wait_if_needed()  # Should trigger rate limit

            # Should see rate limit hit message
            assert "Rate limit hit!" in caplog.text
            assert "waiting" in caplog.text
            assert "Rate limit wait complete" in caplog.text
