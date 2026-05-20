"""Unit tests for service limit configuration support."""

import pytest

from tests.helpers import MockRateLimiter


@pytest.mark.asyncio
async def test_no_service_limits_by_default() -> None:
    """No service limit buckets should exist before headers are received."""
    limiter = MockRateLimiter(((20, 1), (100, 120)))
    assert len(limiter.dynamic) == 0, "Should have no dynamic buckets by default"


@pytest.mark.asyncio
async def test_service_limit_from_header_overrides_nothing() -> None:
    """Service limits from headers create dynamic buckets."""
    limiter = MockRateLimiter(((20, 1), (100, 120)))

    headers = {
        "X-Service-Rate-Limit": "500:60",
        "X-Service-Rate-Limit-Count": "10:60",
    }

    await limiter.update_from_headers(headers, "na1", "match")

    service_keys = [k for k in limiter.dynamic if "service" in k and "500:60" in k]
    assert len(service_keys) > 0, "Should have created service limit buckets"


@pytest.mark.asyncio
async def test_service_limits_isolated_per_region() -> None:
    """App buckets should be isolated per region."""
    limiter = MockRateLimiter(((20, 1), (100, 120)))

    await limiter.acquire("na1", "summoner-v4")
    await limiter.acquire("euw1", "summoner-v4")

    assert "na1" in limiter.app_buckets
    assert "euw1" in limiter.app_buckets
    assert limiter.app_buckets["na1"] is not limiter.app_buckets["euw1"]


@pytest.mark.asyncio
async def test_service_limit_not_duplicated_on_multiple_acquires() -> None:
    """App buckets should not duplicate on repeated acquires."""
    limiter = MockRateLimiter(((20, 1), (100, 120)))

    await limiter.acquire("na1", "summoner-v4")
    await limiter.acquire("na1", "summoner-v4")
    await limiter.acquire("na1", "summoner-v4")

    na1_buckets = limiter.app_buckets.get("na1", [])
    assert len(na1_buckets) == 2  # Two app limits only
