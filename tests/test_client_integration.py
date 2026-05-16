"""Integration tests for NexarClient and RateLimiter."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nexar.client import NexarClient
from nexar.enums import Region


@pytest.mark.asyncio
async def test_client_integrates_rate_limiter() -> None:
    client = NexarClient(riot_api_key="test-api-key", default_region=Region.NA1)

    client.rate_limiter = MagicMock()
    client.rate_limiter.acquire = AsyncMock()
    client.rate_limiter.update_from_headers = AsyncMock()

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"key": "value"}
    mock_response.headers = {
        "X-App-Rate-Limit": "20:1,100:120",
        "X-App-Rate-Limit-Count": "1:1,5:120",
        "Retry-After": "5",
    }
    mock_response.__aenter__.return_value = mock_response
    mock_response.__aexit__.return_value = None

    mock_session = MagicMock()
    mock_session.get.return_value = mock_response
    mock_session.closed = False
    client._session = mock_session

    await client._make_api_call("/lol/summoner/v4/summoners/by-name/test", "na1")

    client.rate_limiter.acquire.assert_called_once_with("na1", "summoner-v4")
    client.rate_limiter.update_from_headers.assert_awaited_once()
    call_args = client.rate_limiter.update_from_headers.await_args
    assert call_args[0][0] == mock_response.headers
    assert call_args[0][1] == "na1"
    assert call_args[0][2] == "summoner-v4"


@pytest.mark.asyncio
async def test_client_updates_rate_limiter_on_429() -> None:
    client = NexarClient(riot_api_key="test-api-key", default_region=Region.NA1)

    client.rate_limiter = MagicMock()
    client.rate_limiter.acquire = AsyncMock()
    client.rate_limiter.release = AsyncMock()
    client.rate_limiter.update_from_headers = AsyncMock()

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

    with patch("asyncio.sleep", new_callable=AsyncMock):
        await client._make_api_call("/test-endpoint", "na1", max_retries=2)

    assert client.rate_limiter.update_from_headers.await_count == 2
