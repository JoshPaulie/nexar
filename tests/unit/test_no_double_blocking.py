"""Test to verify no double-blocking on 429 responses."""

import time

import pytest
from aioresponses import aioresponses

from nexar import NexarClient
from nexar.enums import Region


@pytest.fixture
def simple_client() -> NexarClient:
    return NexarClient(riot_api_key="test-api-key", default_region=Region.NA1)


@pytest.mark.asyncio
async def test_no_double_blocking_on_429(simple_client: NexarClient, mock_aioresponse: aioresponses) -> None:
    url = "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/test-puuid"

    mock_aioresponse.get(
        url,
        status=429,
        headers={"Retry-After": "0.2"},
        payload={"status": {"message": "Rate limit exceeded", "status_code": 429}},
    )

    mock_aioresponse.get(
        url,
        status=200,
        payload={
            "id": "123", "accountId": "456", "puuid": "test-puuid",
            "name": "TestUser", "profileIconId": 1, "revisionDate": 123456789, "summonerLevel": 30,
        },
    )

    t0 = time.time()
    summoner = await simple_client.get_summoner_by_puuid("test-puuid")
    elapsed = time.time() - t0

    assert summoner.puuid == "test-puuid"
    assert 0.1 < elapsed < 0.5, f"Expected ~0.2s total wait (Retry-After), got {elapsed:.3f}s"

    await simple_client.close()


@pytest.mark.asyncio
async def test_rate_limiter_blocks_on_429_headers(simple_client: NexarClient) -> None:
    headers = {
        "Retry-After": "0.2",
        "X-Rate-Limit-Type": "application",
        "X-App-Rate-Limit": "20:1",
        "X-App-Rate-Limit-Count": "1:1",
    }

    await simple_client._ensure_session()
    await simple_client.rate_limiter.update_from_headers(headers, "na1", "summoner-v4")

    start_time = time.time()
    await simple_client.rate_limiter.acquire("na1", "summoner-v4")
    elapsed = time.time() - start_time

    assert 0.15 < elapsed < 0.35, f"Expected ~0.2s block, got {elapsed}s"
    await simple_client.close()


@pytest.mark.asyncio
async def test_client_doesnt_sleep_on_429(simple_client: NexarClient, mock_aioresponse: aioresponses) -> None:
    url = "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/test-puuid"

    mock_aioresponse.get(
        url,
        status=429,
        headers={"Retry-After": "0.1"},
        payload={"status": {"message": "Rate limit exceeded", "status_code": 429}},
    )

    mock_aioresponse.get(
        url,
        status=200,
        payload={
            "id": "123", "accountId": "456", "puuid": "test-puuid",
            "name": "TestUser", "profileIconId": 1, "revisionDate": 123456789, "summonerLevel": 30,
        },
    )

    t0 = time.time()
    summoner = await simple_client.get_summoner_by_puuid("test-puuid")
    elapsed = time.time() - t0

    assert summoner.puuid == "test-puuid"
    assert 0.05 < elapsed < 0.3, f"Expected ~0.1s total wait (Retry-After), got {elapsed:.3f}s"
    await simple_client.close()


@pytest.mark.asyncio
async def test_429_with_multiple_retries(simple_client: NexarClient, mock_aioresponse: aioresponses) -> None:
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
            "id": "123", "accountId": "456", "puuid": "test-puuid",
            "name": "TestUser", "profileIconId": 1, "revisionDate": 123456789, "summonerLevel": 30,
        },
    )

    t0 = time.time()
    summoner = await simple_client.get_summoner_by_puuid("test-puuid")
    elapsed = time.time() - t0

    assert summoner.puuid == "test-puuid"
    assert 0.2 < elapsed < 0.6, f"Expected ~0.3s total wait (2x Retry-After 0.15s), got {elapsed:.3f}s"
    await simple_client.close()
