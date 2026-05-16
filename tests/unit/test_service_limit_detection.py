"""Unit tests for service limit detection from 429 responses."""

import time

import pytest

from tests.helpers import MockRateLimiter


class TestRateLimitTypeDetection:
    @pytest.mark.asyncio
    async def test_explicit_service_limit_header(self) -> None:
        limiter = MockRateLimiter()
        headers = {"X-Rate-Limit-Type": "service", "X-Service-Rate-Limit": "100:60"}
        assert limiter.detect_rate_limit_type(headers) == "service"

    @pytest.mark.asyncio
    async def test_explicit_app_limit_header(self) -> None:
        limiter = MockRateLimiter()
        headers = {"X-Rate-Limit-Type": "application", "X-App-Rate-Limit": "20:1"}
        assert limiter.detect_rate_limit_type(headers) == "app"

    @pytest.mark.asyncio
    async def test_explicit_method_limit_header(self) -> None:
        limiter = MockRateLimiter()
        headers = {"X-Rate-Limit-Type": "method", "X-Method-Rate-Limit": "100:10"}
        assert limiter.detect_rate_limit_type(headers) == "method"

    @pytest.mark.asyncio
    async def test_missing_header_with_service_limit_indicator(self) -> None:
        limiter = MockRateLimiter()
        assert limiter.detect_rate_limit_type({"X-Service-Rate-Limit": "100:60"}) == "service"

    @pytest.mark.asyncio
    async def test_missing_header_with_app_limit_indicator(self) -> None:
        limiter = MockRateLimiter()
        assert limiter.detect_rate_limit_type({"X-App-Rate-Limit": "20:1"}) == "app"

    @pytest.mark.asyncio
    async def test_missing_header_with_method_limit_indicator(self) -> None:
        limiter = MockRateLimiter()
        assert limiter.detect_rate_limit_type({"X-Method-Rate-Limit": "100:10"}) == "method"

    @pytest.mark.asyncio
    async def test_missing_header_no_limit_indicators(self) -> None:
        limiter = MockRateLimiter()
        assert limiter.detect_rate_limit_type({}) == "service"

    @pytest.mark.asyncio
    async def test_case_insensitive_header_matching(self) -> None:
        limiter = MockRateLimiter()
        assert limiter.detect_rate_limit_type({"X-Rate-Limit-Type": "APPLICATION"}) == "app"
        assert limiter.detect_rate_limit_type({"X-Rate-Limit-Type": "Method"}) == "method"
        assert limiter.detect_rate_limit_type({"X-Rate-Limit-Type": "SERVICE"}) == "service"

    @pytest.mark.asyncio
    async def test_multiple_indicators_prioritizes_explicit_header(self) -> None:
        limiter = MockRateLimiter()
        headers = {
            "X-Rate-Limit-Type": "service",
            "X-Service-Rate-Limit": "100:60",
            "X-App-Rate-Limit": "20:1",
            "X-Method-Rate-Limit": "100:10",
        }
        assert limiter.detect_rate_limit_type(headers) == "service"

        headers["X-Rate-Limit-Type"] = "application"
        assert limiter.detect_rate_limit_type(headers) == "app"

    @pytest.mark.asyncio
    async def test_unknown_header_value_defaults_to_app(self) -> None:
        limiter = MockRateLimiter()
        assert limiter.detect_rate_limit_type({"X-Rate-Limit-Type": "unknown_value"}) == "app"

    @pytest.mark.asyncio
    async def test_empty_headers_defaults_to_service(self) -> None:
        limiter = MockRateLimiter()
        assert limiter.detect_rate_limit_type({}) == "service"


class TestRateLimitHandling:
    @pytest.mark.asyncio
    async def test_retry_after_respected(self) -> None:
        limiter = MockRateLimiter()
        headers = {"Retry-After": "120", "X-Service-Rate-Limit": "100:60"}
        start_time = time.time()
        await limiter.update_from_headers(headers, "na1", "summoner-v4")

        for record in limiter.limits.get("na1", {}).values():
            if record.type == "service" and not record.key.startswith("method_"):
                assert 119 < (record.blocked_until - start_time) < 121

    @pytest.mark.asyncio
    async def test_invalid_retry_after_defaults_to_5_seconds(self) -> None:
        limiter = MockRateLimiter()
        headers = {"Retry-After": "not_a_number"}
        start_time = time.time()
        await limiter.update_from_headers(headers, "na1", "summoner-v4")

        for record in limiter.limits.get("na1", {}).values():
            if record.type == "app":
                assert 4 < (record.blocked_until - start_time) < 6
