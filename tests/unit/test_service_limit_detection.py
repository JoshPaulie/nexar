"""Unit tests for service limit detection from 429 responses."""

import time

import pytest

from tests.helpers import MockRateLimiter


class TestRateLimitTypeDetection:
    @pytest.mark.asyncio
    async def test_explicit_service_limit_header(self) -> None:
        limiter = MockRateLimiter()
        headers = {"X-Rate-Limit-Type": "service", "X-Service-Rate-Limit": "100:60"}
        result = limiter.detect_rate_limit_type(headers)
        assert result == ("service", True)

    @pytest.mark.asyncio
    async def test_explicit_app_limit_header(self) -> None:
        limiter = MockRateLimiter()
        headers = {"X-Rate-Limit-Type": "application", "X-App-Rate-Limit": "20:1"}
        result = limiter.detect_rate_limit_type(headers)
        assert result == ("app", True)

    @pytest.mark.asyncio
    async def test_explicit_method_limit_header(self) -> None:
        limiter = MockRateLimiter()
        headers = {"X-Rate-Limit-Type": "method", "X-Method-Rate-Limit": "100:10"}
        result = limiter.detect_rate_limit_type(headers)
        assert result == ("method", True)

    @pytest.mark.asyncio
    async def test_missing_header_with_service_limit_indicator(self) -> None:
        limiter = MockRateLimiter()
        result = limiter.detect_rate_limit_type({"X-Service-Rate-Limit": "100:60"})
        assert result == ("service", False)

    @pytest.mark.asyncio
    async def test_missing_header_with_app_limit_indicator(self) -> None:
        limiter = MockRateLimiter()
        result = limiter.detect_rate_limit_type({"X-App-Rate-Limit": "20:1"})
        assert result == ("app", False)

    @pytest.mark.asyncio
    async def test_missing_header_with_method_limit_indicator(self) -> None:
        limiter = MockRateLimiter()
        result = limiter.detect_rate_limit_type({"X-Method-Rate-Limit": "100:10"})
        assert result == ("method", False)

    @pytest.mark.asyncio
    async def test_missing_header_no_limit_indicators(self) -> None:
        limiter = MockRateLimiter()
        result = limiter.detect_rate_limit_type({})
        assert result == ("service", False)

    @pytest.mark.asyncio
    async def test_case_insensitive_header_matching(self) -> None:
        limiter = MockRateLimiter()
        assert limiter.detect_rate_limit_type({"X-Rate-Limit-Type": "APPLICATION"}) == ("app", True)
        assert limiter.detect_rate_limit_type({"X-Rate-Limit-Type": "Method"}) == ("method", True)
        assert limiter.detect_rate_limit_type({"X-Rate-Limit-Type": "SERVICE"}) == ("service", True)

    @pytest.mark.asyncio
    async def test_multiple_indicators_prioritizes_explicit_header(self) -> None:
        limiter = MockRateLimiter()
        headers = {
            "X-Rate-Limit-Type": "service",
            "X-Service-Rate-Limit": "100:60",
            "X-App-Rate-Limit": "20:1",
            "X-Method-Rate-Limit": "100:10",
        }
        assert limiter.detect_rate_limit_type(headers) == ("service", True)

        headers["X-Rate-Limit-Type"] = "application"
        assert limiter.detect_rate_limit_type(headers) == ("app", True)

    @pytest.mark.asyncio
    async def test_unknown_header_value_defaults_to_app(self) -> None:
        limiter = MockRateLimiter()
        assert limiter.detect_rate_limit_type({"X-Rate-Limit-Type": "unknown_value"}) == ("app", True)

    @pytest.mark.asyncio
    async def test_empty_headers_defaults_to_service(self) -> None:
        limiter = MockRateLimiter()
        assert limiter.detect_rate_limit_type({}) == ("service", False)


class TestRateLimitHandling:
    @pytest.mark.asyncio
    async def test_retry_after_respected(self) -> None:
        """Retry-After header should set blocked_until on the appropriate bucket."""
        limiter = MockRateLimiter()
        headers = {"Retry-After": "120", "X-Service-Rate-Limit": "100:60"}
        start_time = time.time()
        await limiter.update_from_headers(headers, "na1", "summoner-v4")

        # Should have blocked app and dynamic buckets for the region
        blocked_count = sum(
            1 for k, v in limiter.blocked.items()
            if "na1" in k and v > start_time
        )
        assert blocked_count > 0, "Should have blocked entries for the region"

    @pytest.mark.asyncio
    async def test_invalid_retry_after_defaults_to_5_seconds(self) -> None:
        """Invalid Retry-After should default to 5 seconds blocking."""
        limiter = MockRateLimiter()
        headers = {"Retry-After": "not_a_number"}
        start_time = time.time()
        await limiter.update_from_headers(headers, "na1", "summoner-v4")

        for key, blocked_until in limiter.blocked.items():
            if "na1" in key:
                assert 4 < (blocked_until - start_time) < 6, (
                    f"Blocked {key} should be ~5s, got {blocked_until - start_time:.1f}s"
                )

    @pytest.mark.asyncio
    async def test_ambiguous_429_blocks_all_records(self) -> None:
        """When X-Rate-Limit-Type is absent, all buckets for the region are blocked."""
        limiter = MockRateLimiter()
        # Seed with some records of each type
        await limiter.update_from_headers(
            {
                "X-App-Rate-Limit": "20:1,100:120",
                "X-App-Rate-Limit-Count": "0:1,0:120",
            },
            "na1",
            "summoner-v4",
        )
        await limiter.update_from_headers(
            {
                "X-Service-Rate-Limit": "50:10",
                "X-Service-Rate-Limit-Count": "0:10",
            },
            "na1",
            "summoner-v4",
        )

        # Ambiguous 429: no X-Rate-Limit-Type
        headers = {
            "Retry-After": "2",
            "X-App-Rate-Limit": "20:1,100:120",
            "X-App-Rate-Limit-Count": "20:1,100:120",
        }
        start_time = time.time()
        await limiter.update_from_headers(headers, "na1", "summoner-v4")

        blocked_for_region = {
            k: v for k, v in limiter.blocked.items() if "na1" in k
        }
        assert len(blocked_for_region) > 0, "Should have blocked entries for na1"
        for key, blocked_until in blocked_for_region.items():
            assert 1 < (blocked_until - start_time) < 3, (
                f"Blocked {key} should be ~2s, got {blocked_until - start_time:.1f}s"
            )
