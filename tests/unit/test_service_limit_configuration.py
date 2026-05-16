"""Unit tests for service limit configuration support."""

import pytest

from tests.helpers import MockRateLimiter


@pytest.mark.asyncio
async def test_no_service_limits_by_default() -> None:
    limiter = MockRateLimiter(((20, 1), (100, 120)))
    assert not any(
        r.type == "service"
        for region_limits in limiter.limits.values()
        for r in region_limits.values()
    )


@pytest.mark.asyncio
async def test_service_limit_from_header_overrides_nothing() -> None:
    limiter = MockRateLimiter(((20, 1), (100, 120)))

    headers = {
        "X-Service-Rate-Limit": "500:60",
        "X-Service-Rate-Limit-Count": "10:60",
    }

    await limiter.update_from_headers(headers, "na1", "match")

    service_limits = {
        k: v for k, v in limiter.limits.get("na1", {}).items()
        if v.type == "service" and "500:60" in k
    }
    assert len(service_limits) > 0


@pytest.mark.asyncio
async def test_service_limits_isolated_per_region() -> None:
    limiter = MockRateLimiter(((20, 1), (100, 120)))

    await limiter.acquire("na1", "summoner-v4")
    await limiter.acquire("euw1", "summoner-v4")

    assert len(limiter.limits["na1"]) > 0
    assert len(limiter.limits["euw1"]) > 0

    na1_app = [r for r in limiter.limits["na1"].values() if r.type == "app"]
    euw1_app = [r for r in limiter.limits["euw1"].values() if r.type == "app"]

    if na1_app and euw1_app:
        assert "na1" in na1_app[0].key
        assert "euw1" in euw1_app[0].key


@pytest.mark.asyncio
async def test_service_limit_not_duplicated_on_multiple_acquires() -> None:
    limiter = MockRateLimiter(((20, 1), (100, 120)))

    await limiter.acquire("na1", "summoner-v4")
    await limiter.acquire("na1", "summoner-v4")
    await limiter.acquire("na1", "summoner-v4")

    na1_keys = list(limiter.limits.get("na1", {}).keys())
    assert len(na1_keys) == len(set(na1_keys))  # No duplicates
    assert len(na1_keys) == 2  # Two app limits only
