"""Integration tests for NexarClient and RateLimiter."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from nexar.cache import NO_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import Region


@pytest.mark.asyncio
async def test_client_goes_through_rate_limiter() -> None:
    client = NexarClient(riot_api_key="test-api-key", default_region=Region.NA1, cache_config=NO_CACHE_CONFIG)

    client.rate_limiter = MagicMock()
    client.rate_limiter.acquire = AsyncMock()

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"key": "value"}
    mock_response.headers = {}
    mock_response.__aenter__.return_value = mock_response
    mock_response.__aexit__.return_value = None

    mock_session = MagicMock()
    mock_session.get.return_value = mock_response
    mock_session.closed = False
    client._session = mock_session

    await client._make_api_call("/lol/summoner/v4/summoners/by-name/test", "na1")

    client.rate_limiter.acquire.assert_called_once_with("na1")


@pytest.mark.asyncio
async def test_client_blocks_limiter_on_429() -> None:
    client = NexarClient(riot_api_key="test-api-key", default_region=Region.NA1, cache_config=NO_CACHE_CONFIG)

    client.rate_limiter = MagicMock()
    client.rate_limiter.acquire = AsyncMock()

    mock_response_429 = AsyncMock()
    mock_response_429.status = 429
    mock_response_429.headers = {"Retry-After": "1"}
    mock_response_429.__aenter__.return_value = mock_response_429
    mock_response_429.__aexit__.return_value = None

    mock_response_200 = AsyncMock()
    mock_response_200.status = 200
    mock_response_200.json.return_value = {}
    mock_response_200.headers = {}
    mock_response_200.__aenter__.return_value = mock_response_200
    mock_response_200.__aexit__.return_value = None

    mock_session = MagicMock()
    mock_session.get.side_effect = [mock_response_429, mock_response_200]
    mock_session.closed = False
    client._session = mock_session

    await client._make_api_call("/test-endpoint", "na1", max_retries=2)

    # The 429 must block the region for the Retry-After duration, once.
    client.rate_limiter.block.assert_called_once_with("na1", 1.0)


@pytest.mark.asyncio
async def test_client_seeds_rate_limiter_from_fresh_responses() -> None:
    client = NexarClient(riot_api_key="test-api-key", default_region=Region.NA1, cache_config=NO_CACHE_CONFIG)

    client.rate_limiter = MagicMock()
    client.rate_limiter.acquire = AsyncMock()

    def make_response(count_header: str | None, *, from_cache: bool = False) -> AsyncMock:
        response = AsyncMock()
        response.status = 200
        response.json.return_value = {"key": "value"}
        headers = {"X-App-Rate-Limit-Count": count_header} if count_header else {}
        response.headers = headers
        response.from_cache = from_cache
        response.__aenter__.return_value = response
        response.__aexit__.return_value = None
        return response

    session = MagicMock()
    session.closed = False
    client._session = session

    # Fresh response with count header: oriented with parsed counts
    session.get.return_value = make_response("5:1,90:120")
    await client._make_api_call("/one", "na1")
    client.rate_limiter.seed_from_counts.assert_called_once_with("na1", {1: 5, 120: 90})

    # Every fresh response hands the counts over; the limiter no-ops after the first
    session.get.return_value = make_response("6:1,91:120")
    await client._make_api_call("/two", "na1")
    assert client.rate_limiter.seed_from_counts.call_count == 2

    # Cached responses make no API call and must not orient
    client.rate_limiter.seed_from_counts.reset_mock()
    session.get.return_value = make_response("6:1,91:120", from_cache=True)
    await client._make_api_call("/cached", "na1")
    client.rate_limiter.seed_from_counts.assert_not_called()

    # Malformed count header: no orientation, no crash
    session.get.return_value = make_response("garbage")
    await client._make_api_call("/bad-header", "na1")
    client.rate_limiter.seed_from_counts.assert_not_called()
