"""Tests for rate limit configuration options."""

import time

import pytest
from aioresponses import aioresponses

from nexar import NexarClient
from nexar.cache import NO_CACHE_CONFIG
from nexar.enums import Region
from nexar.rate_limiter import RateLimiter, _validate_rate_limit


def test_validate_rate_limit_valid() -> None:
    """Valid budgets at both standard tiers pass validation."""
    _validate_rate_limit(20, 1)
    _validate_rate_limit(500, 10)
    _validate_rate_limit(30000, 600)


@pytest.mark.parametrize(
    ("limit", "window", "match"),
    [
        (0, 1, "must be positive"),
        (-5, 1, "must be positive"),
        (20, 0, "must be positive"),
        (20, -5, "must be positive"),
        (2_000_000, 1, "suspiciously high"),
        (100, 90_000, "suspiciously long"),
    ],
)
def test_invalid_app_rate_limits_are_rejected(limit: int, window: int, match: str) -> None:
    """Invalid (limit, window) budgets raise at RateLimiter construction instead of being accepted."""
    with pytest.raises(ValueError, match=match):
        RateLimiter(((limit, window),))


@pytest.mark.asyncio
async def test_custom_app_rate_limits_pace_calls(mock_aioresponse: aioresponses) -> None:
    """The app_rate_limits argument actually wires: a (1, 1) budget paces the second call."""
    client = NexarClient(
        riot_api_key="test",
        default_region=Region.NA1,
        app_rate_limits=((1, 1),),
        cache_config=NO_CACHE_CONFIG,
    )
    url = "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/p1"
    mock_aioresponse.get(
        url,
        payload={"id": "s1", "puuid": "p1", "profileIconId": 1, "revisionDate": 1, "summonerLevel": 30},
        repeat=True,
    )

    start = time.perf_counter()
    await client.get_summoner_by_puuid("p1")
    first_elapsed = time.perf_counter() - start
    assert first_elapsed < 0.5

    start = time.perf_counter()
    await client.get_summoner_by_puuid("p1")
    second_elapsed = time.perf_counter() - start
    assert 0.9 <= second_elapsed < 1.3

    await client.close()
