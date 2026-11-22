"""Test to verify no double-blocking on 429 responses."""

import time
from collections.abc import AsyncGenerator

import pytest
from aioresponses import aioresponses

from nexar import NexarClient
from nexar.cache import NO_CACHE_CONFIG
from nexar.enums import Region


@pytest.fixture
async def simple_client() -> AsyncGenerator[NexarClient]:
    # Use only the 20/1s bucket to avoid ~1.2s refill from the 100/120s bucket
    # interfering with timing assertions in these tests. The session closes
    # after each test, red or green, so a failing row cannot hang the run.
    client = NexarClient(
        riot_api_key="test-api-key",
        default_region=Region.NA1,
        app_rate_limits=((20, 1),),
        cache_config=NO_CACHE_CONFIG,
    )
    yield client
    await client.close()


def _register_summoner_responses(mock_aioresponse: aioresponses, url: str, retry_after: str) -> None:
    mock_aioresponse.get(
        url,
        status=429,
        headers={"Retry-After": retry_after},
        payload={"status": {"message": "Rate limit exceeded", "status_code": 429}},
    )
    mock_aioresponse.get(
        url,
        status=200,
        payload={
            "id": "123",
            "accountId": "456",
            "puuid": "test-puuid",
            "name": "TestUser",
            "profileIconId": 1,
            "revisionDate": 123456789,
            "summonerLevel": 30,
        },
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("retry_after", "upper_bound"),
    [(0.2, 0.26), (0.1, 0.13)],
    ids=["one-block", "short-block"],
)
async def test_no_double_blocking_on_429(
    simple_client: NexarClient,
    mock_aioresponse: aioresponses,
    retry_after: float,
    upper_bound: float,
) -> None:
    """A 429 blocks exactly one Retry-After: a stacked second wait blows the 1.3x bound."""
    url = "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/test-puuid"
    _register_summoner_responses(mock_aioresponse, url, str(retry_after))

    t0 = time.monotonic()
    summoner = await simple_client.get_summoner_by_puuid("test-puuid")
    elapsed = time.monotonic() - t0

    assert summoner.puuid == "test-puuid"
    assert 0.05 < elapsed < upper_bound, f"Expected ~{retry_after}s wait, got {elapsed:.3f}s"

    await simple_client.close()


@pytest.mark.asyncio
async def test_429_with_multiple_retries(simple_client: NexarClient, mock_aioresponse: aioresponses) -> None:
    """Two 429s block twice (once per response) and then succeed — the row that catches stacked waits."""
    url = "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/test-puuid"

    mock_aioresponse.get(
        url,
        status=429,
        headers={"Retry-After": "0.15"},
        payload={"status": {"message": "Rate limit exceeded", "status_code": 429}},
    )
    mock_aioresponse.get(
        url,
        status=429,
        headers={"Retry-After": "0.15"},
        payload={"status": {"message": "Rate limit exceeded", "status_code": 429}},
    )
    mock_aioresponse.get(
        url,
        status=200,
        payload={
            "id": "123",
            "accountId": "456",
            "puuid": "test-puuid",
            "name": "TestUser",
            "profileIconId": 1,
            "revisionDate": 123456789,
            "summonerLevel": 30,
        },
    )

    t0 = time.monotonic()
    summoner = await simple_client.get_summoner_by_puuid("test-puuid")
    elapsed = time.monotonic() - t0

    assert summoner.puuid == "test-puuid"
    assert 0.2 < elapsed < 0.6, f"Expected ~0.3s total wait (2x Retry-After 0.15s), got {elapsed:.3f}s"
    await simple_client.close()
