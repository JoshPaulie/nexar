"""Tests for NexarClient using aioresponses."""

import asyncio
import re
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp_client_cache.session import CachedSession
from aioresponses import aioresponses

from nexar import NexarClient
from nexar.cache import CacheConfig
from nexar.enums import Region
from nexar.exceptions import (
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    RiotAPIError,
    UnauthorizedError,
)

if TYPE_CHECKING:
    from nexar.models import Player, Summoner


@pytest.fixture
def fresh_client() -> NexarClient:
    return NexarClient(riot_api_key="test-api-key", default_region=Region.NA1)


@pytest.mark.asyncio
async def test_client_initialization(fresh_client: NexarClient) -> None:
    assert fresh_client.default_region == Region.NA1
    assert fresh_client.riot_api_key == "test-api-key"
    await fresh_client.close()


@pytest.mark.asyncio
async def test_get_summoner_by_puuid(fresh_client: NexarClient, mock_aioresponse: aioresponses) -> None:
    mock_aioresponse.get(
        "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/789",
        payload={
            "id": "123", "accountId": "456", "puuid": "789",
            "name": "TestUser", "profileIconId": 1, "revisionDate": 123456789, "summonerLevel": 30,
        },
    )
    summoner: Summoner = await fresh_client.get_summoner_by_puuid("789")
    assert summoner.summoner_id == "123"
    assert summoner.puuid == "789"
    await fresh_client.close()


@pytest.mark.asyncio
async def test_error_handling_404(fresh_client: NexarClient, mock_aioresponse: aioresponses) -> None:
    mock_aioresponse.get(
        "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/UnknownUser",
        status=404,
        payload={"status": {"message": "Not Found", "status_code": 404}},
    )
    with pytest.raises(NotFoundError, match="Not Found"):
        await fresh_client.get_summoner_by_puuid("UnknownUser")
    await fresh_client.close()


@pytest.mark.asyncio
async def test_error_handling_401(fresh_client: NexarClient, mock_aioresponse: aioresponses) -> None:
    mock_aioresponse.get(
        "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/test/tag",
        status=401,
        payload={"status": {"message": "Unauthorized", "status_code": 401}},
    )
    with pytest.raises(UnauthorizedError):
        await fresh_client.get_riot_account("test", "tag")
    await fresh_client.close()


@pytest.mark.asyncio
async def test_error_handling_403(fresh_client: NexarClient, mock_aioresponse: aioresponses) -> None:
    mock_aioresponse.get(
        "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/test/tag",
        status=403,
        payload={"status": {"message": "Forbidden", "status_code": 403}},
    )
    with pytest.raises(ForbiddenError):
        await fresh_client.get_riot_account("test", "tag")
    await fresh_client.close()


@pytest.mark.asyncio
async def test_error_handling_429(fresh_client: NexarClient, mock_aioresponse: aioresponses) -> None:
    url = "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/test/tag"
    for _ in range(6):
        mock_aioresponse.get(
            url,
            status=429,
            headers={"Retry-After": "0.1"},
            payload={"status": {"message": "Rate limit exceeded", "status_code": 429}},
        )

    async def mock_sleep(_: float) -> None:
        pass

    with pytest.MonkeyPatch.context() as m:
        m.setattr(asyncio, "sleep", mock_sleep)
        with pytest.raises(RateLimitError, match="Max retries .5. exceeded"):
            await fresh_client.get_riot_account("test", "tag")
    await fresh_client.close()


@pytest.mark.asyncio
async def test_cache_info_empty(fresh_client: NexarClient) -> None:
    await fresh_client._ensure_session()
    info = await fresh_client.get_cache_info()
    assert info["enabled"] is True
    assert "cached_responses" in info
    await fresh_client.close()


@pytest.mark.asyncio
async def test_cache_hit() -> None:
    config = CacheConfig(enabled=True, backend="memory", expire_after=60)
    client = NexarClient(riot_api_key="key", default_region=Region.NA1, cache_config=config)

    await client._ensure_session()

    response_data = {
        "metadata": {"matchId": "M_123", "dataVersion": "2", "participants": ["p1", "p2"]},
        "info": {
            "gameCreation": 123456789, "gameDuration": 1234, "gameEndTimestamp": 1234567890,
            "gameId": 12345, "gameMode": "CLASSIC", "gameName": "test",
            "gameStartTimestamp": 123456789, "gameType": "MATCHED_GAME", "gameVersion": "1.0",
            "mapId": 11, "participants": [], "platformId": "NA1", "queueId": 420,
            "teams": [], "tournamentCode": "",
        },
    }

    if client._session and isinstance(client._session, CachedSession):
        mock_cached_resp = MagicMock()
        mock_cached_resp.status = 200
        mock_cached_resp.json = AsyncMock(return_value=response_data)
        client._session.cache.get_response = AsyncMock(return_value=mock_cached_resp)

        match = await client.get_match("M_123")
        assert match.metadata.match_id == "M_123"
        client._session.cache.get_response.assert_called_once()

    await client.close()


@pytest.mark.asyncio
async def test_clear_cache() -> None:
    config = CacheConfig(enabled=True, backend="memory")
    client = NexarClient(riot_api_key="key", cache_config=config)
    await client._ensure_session()
    await client.clear_cache()
    info = await client.get_cache_info()
    assert info.get("cached_responses", 0) == 0
    await client.close()


@pytest.mark.asyncio
async def test_get_match_ids_params(fresh_client: NexarClient, mock_aioresponse: aioresponses) -> None:
    mock_aioresponse.get(
        re.compile(r"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/puuid/ids\?.*"),
        payload=["NA1_1", "NA1_2"],
    )
    ids = await fresh_client.get_match_ids_by_puuid("puuid", start=10, count=5, queue=420, match_type="ranked")
    assert len(ids) == 2
    assert ids[0] == "NA1_1"
    await fresh_client.close()


@pytest.mark.asyncio
async def test_high_level_get_player(fresh_client: NexarClient, mock_aioresponse: aioresponses) -> None:
    mock_aioresponse.get(
        "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/GameName/TagLine",
        payload={"gameName": "GameName", "tagLine": "TagLine", "puuid": "p1"},
    )
    mock_aioresponse.get(
        "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/p1",
        payload={
            "id": "s1", "puuid": "p1", "accountId": "a1",
            "name": "GameName", "profileIconId": 1,
            "revisionDate": 1, "summonerLevel": 100,
        },
    )
    player: Player = await fresh_client.get_player(game_name="GameName", tag_line="TagLine")
    assert player.game_name == "GameName"
    assert player.puuid == "p1"
    await fresh_client.close()
