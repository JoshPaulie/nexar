"""Test for region isolation in rate limiting."""

import pytest

from tests.helpers import MockRateLimiter


@pytest.mark.asyncio
async def test_rate_limit_per_platform_region() -> None:
    limiter = MockRateLimiter(((2, 10), (10, 60)), safety_margin=0)

    await limiter.acquire("na1", "summoner-v4")
    await limiter.acquire("na1", "summoner-v4")
    await limiter.acquire("br1", "summoner-v4")
    await limiter.acquire("br1", "summoner-v4")

    na1_keys = set(limiter.limits["na1"].keys())
    br1_keys = set(limiter.limits["br1"].keys())

    assert len(na1_keys) > 0, "NA1 should have rate limit records"
    assert len(br1_keys) > 0, "BR1 should have rate limit records"

    assert any("na1" in key for key in na1_keys), "NA1 limits should use 'na1' in key"
    assert any("br1" in key for key in br1_keys), "BR1 limits should use 'br1' in key"
    assert na1_keys.isdisjoint(br1_keys), "NA1 and BR1 should have separate rate limit buckets"
    assert not any("americas" in key for key in na1_keys | br1_keys), (
        "Keys should use platform regions not routing regions"
    )


@pytest.mark.asyncio
async def test_multiple_regions_isolated() -> None:
    limiter = MockRateLimiter(((1, 10), (10, 60)), safety_margin=0)

    regions = ["na1", "br1", "euw1", "kr", "oc1"]
    for region in regions:
        await limiter.acquire(region, "match-v5")

    for region in regions:
        assert region in limiter.limits, f"{region} should have rate limit records"
        for key in limiter.limits[region]:
            assert region in key, f"{region} limit key should contain region code"
            for other_region in regions:
                if other_region != region:
                    assert other_region not in key, (
                        f"{region} limit should not contain other region code {other_region}"
                    )
