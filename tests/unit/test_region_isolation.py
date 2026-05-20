"""Test for region isolation in rate limiting."""

import pytest

from tests.helpers import MockRateLimiter


@pytest.mark.asyncio
async def test_rate_limit_per_platform_region() -> None:
    """Regions should have separate app-level rate limit buckets."""
    limiter = MockRateLimiter(((2, 10), (10, 60)), safety_margin=0)

    await limiter.acquire("na1", "summoner-v4")
    await limiter.acquire("na1", "summoner-v4")
    await limiter.acquire("br1", "summoner-v4")
    await limiter.acquire("br1", "summoner-v4")

    assert "na1" in limiter.app_buckets, "NA1 should have app buckets"
    assert "br1" in limiter.app_buckets, "BR1 should have app buckets"
    assert limiter.app_buckets["na1"] is not limiter.app_buckets["br1"], (
        "NA1 and BR1 should have separate rate limit buckets"
    )


@pytest.mark.asyncio
async def test_multiple_regions_isolated() -> None:
    """Each region should get its own independent rate limit buckets."""
    limiter = MockRateLimiter(((1, 10), (10, 60)), safety_margin=0)

    regions = ["na1", "br1", "euw1", "kr", "oc1"]
    for region in regions:
        await limiter.acquire(region, "match-v5")

    for region in regions:
        assert region in limiter.app_buckets, f"{region} should have app buckets"

    # Each region should have separate bucket instances
    bucket_sets = [id(limiter.app_buckets[r]) for r in regions]
    assert len(set(bucket_sets)) == len(regions), "All regions should have distinct bucket lists"
