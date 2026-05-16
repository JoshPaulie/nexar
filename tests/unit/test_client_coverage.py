"""Coverage-filling tests for NexarClient."""

import os
import re
from datetime import UTC, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from nexar.client import NexarClient
from nexar.enums import MatchType, Queue, Region
from nexar.exceptions import RateLimitError, RiotAPIError


@pytest.fixture
def client() -> NexarClient:
    return NexarClient(riot_api_key="test-key", default_region=Region.NA1)


@pytest.mark.asyncio
async def test_context_manager(client: NexarClient) -> None:
    async with client as c:
        assert c is client
        assert c._session is not None
        assert not c._session.closed
    assert client._session is not None
    assert client._session.closed


@pytest.mark.asyncio
async def test_get_league_entries_by_puuid(client: NexarClient, mock_aioresponse: MagicMock) -> None:
    mock_aioresponse.get(
        "https://na1.api.riotgames.com/lol/league/v4/entries/by-puuid/test-puuid",
        payload=[
            {
                "leagueId": "test-league",
                "queueType": "RANKED_SOLO_5x5",
                "tier": "GOLD",
                "rank": "I",
                "summonerId": "test-summoner",
                "summonerName": "Test Summoner",
                "leaguePoints": 100,
                "wins": 10,
                "losses": 5,
                "veteran": False,
                "inactive": False,
                "freshBlood": False,
                "hotStreak": False,
                "puuid": "test-puuid",
            },
        ],
    )

    entries = await client.get_league_entries_by_puuid("test-puuid")
    assert len(entries) == 1
    assert entries[0].queue_type == Queue.RANKED_SOLO_5x5
    assert entries[0].tier.value == "GOLD"
    await client.close()


@pytest.mark.asyncio
async def test_get_match_ids_validation_error(client: NexarClient) -> None:
    with pytest.raises(ValueError, match="count must be between 0 and 100"):
        await client.get_match_ids_by_puuid("test-puuid", count=101)
    await client.close()


@pytest.mark.asyncio
async def test_get_match_ids_int_times(client: NexarClient, mock_aioresponse: MagicMock) -> None:
    mock_aioresponse.get(
        "https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/test-puuid/ids?endTime=1600000000&startTime=1500000000",
        payload=["NA1_1", "NA1_2"],
    )
    match_ids = await client.get_match_ids_by_puuid("test-puuid", start_time=1500000000, end_time=1600000000)
    assert len(match_ids) == 2
    await client.close()


@pytest.mark.asyncio
async def test_get_match_ids_datetime_times(client: NexarClient, mock_aioresponse: MagicMock) -> None:
    start = datetime.fromtimestamp(1500000000, tz=UTC)
    end = datetime.fromtimestamp(1600000000, tz=UTC)
    mock_aioresponse.get(
        "https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/test-puuid/ids?endTime=1600000000&startTime=1500000000",
        payload=["NA1_1", "NA1_2"],
    )
    match_ids = await client.get_match_ids_by_puuid("test-puuid", start_time=start, end_time=end)
    assert len(match_ids) == 2
    await client.close()


@pytest.mark.asyncio
async def test_get_players(client: NexarClient, mock_aioresponse: MagicMock) -> None:
    mock_aioresponse.get(
        "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/Player1/TAG",
        payload={"puuid": "p1", "gameName": "Player1", "tagLine": "TAG"},
    )
    mock_aioresponse.get(
        "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/Player2/TAG",
        payload={"puuid": "p2", "gameName": "Player2", "tagLine": "TAG"},
    )
    mock_aioresponse.get(
        "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/p1",
        payload={"id": "s1", "puuid": "p1", "accountId": "a1", "name": "Player1", "profileIconId": 1, "revisionDate": 1, "summonerLevel": 30},
    )
    mock_aioresponse.get(
        "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/p2",
        payload={"id": "s2", "puuid": "p2", "accountId": "a2", "name": "Player2", "profileIconId": 1, "revisionDate": 1, "summonerLevel": 30},
    )
    players = await client.get_players(["Player1#TAG", "Player2#TAG"])
    assert len(players) == 2
    assert players[0].game_name == "Player1"
    assert players[1].game_name == "Player2"
    await client.close()


@pytest.mark.asyncio
async def test_get_cache_info_details(client: NexarClient) -> None:
    await client._ensure_session()
    mock_cache = MagicMock()
    mock_cache.__len__ = MagicMock(return_value=5)
    mock_cache.size = 1024
    mock_cache._close_if_enabled = AsyncMock()
    assert client._session is not None
    client._session.cache = mock_cache
    info = await client.get_cache_info()
    assert info["cached_responses"] == 5
    assert info["cache_size"] == 1024
    await client.close()


@pytest.mark.asyncio
async def test_stats_and_logging(client: NexarClient) -> None:
    await client._ensure_session()
    from nexar.client import CallStats

    stats = client.get_api_call_stats()
    assert isinstance(stats, CallStats)
    client.print_api_call_summary()
    await client.close()


@pytest.mark.asyncio
async def test_ensure_session_no_cache() -> None:
    import aiohttp_client_cache.session

    from nexar.cache import CacheConfig

    config = CacheConfig(enabled=False)
    client = NexarClient(riot_api_key="key", cache_config=config, default_region=Region.NA1)
    await client._ensure_session()
    assert not isinstance(client._session, aiohttp_client_cache.session.CachedSession)
    assert isinstance(client._session, aiohttp.ClientSession)
    await client.close()


@pytest.mark.asyncio
async def test_client_error_handling(client: NexarClient, mock_aioresponse: MagicMock) -> None:
    mock_aioresponse.get(
        "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/fail",
        exception=aiohttp.ClientError("Connection failed"),
    )
    with pytest.raises(RiotAPIError, match="Request failed"):
        await client.get_summoner_by_puuid("fail")
    await client.close()


@pytest.mark.asyncio
async def test_malformed_error_response(client: NexarClient, mock_aioresponse: MagicMock) -> None:
    mock_aioresponse.get(
        "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/fail",
        status=400,
        body="Bad Request",
    )
    with pytest.raises(RiotAPIError, match="Bad Request"):
        await client.get_summoner_by_puuid("fail")
    await client.close()


@pytest.mark.asyncio
async def test_resolve_region_error(client: NexarClient) -> None:
    client.default_region = None
    with pytest.raises(ValueError, match="A region must be provided"):
        await client.get_summoner_by_puuid("test")
    await client.close()


@pytest.mark.asyncio
async def test_debug_print_response(client: NexarClient, mock_aioresponse: MagicMock, capsys: pytest.CaptureFixture) -> None:
    with patch.dict(os.environ, {"NEXAR_DEBUG_RESPONSES": "1"}):
        mock_aioresponse.get(
            "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/test",
            payload={"id": "test", "puuid": "test-puuid", "profileIconId": 1, "revisionDate": 123456789, "summonerLevel": 100},
        )
        await client.get_summoner_by_puuid("test")
        captured = capsys.readouterr()
        assert "DEBUG: API Response" in captured.out
        assert "Response Data:" in captured.out
    await client.close()


@pytest.mark.asyncio
async def test_get_match_ids_all_params(client: NexarClient, mock_aioresponse: MagicMock) -> None:
    mock_aioresponse.get(
        "https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/test-puuid/ids?count=5&endTime=1600000000&queue=420&start=10&startTime=1500000000&type=ranked",
        payload=["NA1_1"],
    )
    match_ids = await client.get_match_ids_by_puuid(
        "test-puuid",
        start_time=1500000000,
        end_time=1600000000,
        queue=Queue.RANKED_SOLO_5x5,
        match_type=MatchType.RANKED,
        start=10,
        count=5,
    )
    assert len(match_ids) == 1
    await client.close()


@pytest.mark.asyncio
async def test_get_match(client: NexarClient, mock_aioresponse: MagicMock) -> None:
    response_data = {
        "metadata": {"matchId": "NA1_12345", "dataVersion": "2", "participants": ["p1", "p2"]},
        "info": {
            "gameCreation": 123456789,
            "gameDuration": 1234,
            "gameEndTimestamp": 1234567890,
            "gameId": 12345,
            "gameMode": "CLASSIC",
            "gameName": "test",
            "gameStartTimestamp": 123456789,
            "gameType": "MATCHED_GAME",
            "gameVersion": "1.0",
            "mapId": 11,
            "participants": [],
            "platformId": "NA1",
            "queueId": 420,
            "teams": [],
            "tournamentCode": "",
        },
    }
    mock_aioresponse.get(
        "https://americas.api.riotgames.com/lol/match/v5/matches/NA1_12345",
        payload=response_data,
    )
    match = await client.get_match("NA1_12345")
    assert match.metadata.match_id == "NA1_12345"
    await client.close()


@pytest.mark.asyncio
async def test_get_player_convenience(client: NexarClient, mock_aioresponse: MagicMock) -> None:
    mock_aioresponse.get(
        "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/Game/Tag",
        payload={"puuid": "p1", "gameName": "Game", "tagLine": "Tag"},
    )
    mock_aioresponse.get(
        "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/p1",
        payload={"id": "s1", "puuid": "p1", "accountId": "a1", "name": "Game", "profileIconId": 1, "revisionDate": 1, "summonerLevel": 30},
    )
    player = await client.get_player("Game", "Tag")
    assert player.game_name == "Game"
    await client.close()


@pytest.mark.asyncio
async def test_clear_cache_real(client: NexarClient) -> None:
    await client._ensure_session()
    await client.clear_cache()
    await client.close()


@pytest.mark.asyncio
async def test_cache_info_exception(client: NexarClient) -> None:
    await client._ensure_session()
    mock_cache = MagicMock()
    mock_cache.__len__.side_effect = TypeError("Fail")
    mock_cache._close_if_enabled = AsyncMock()
    assert client._session is not None
    client._session.cache = mock_cache
    info = await client.get_cache_info()
    assert info["cached_responses"] == 0
    await client.close()


@pytest.mark.asyncio
async def test_retry_logic_429(client: NexarClient, mock_aioresponse: MagicMock) -> None:
    url = "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/retry"
    mock_aioresponse.get(url, status=429, headers={"Retry-After": "0.1"}, payload={"status": {"message": "Rate limit", "status_code": 429}})
    mock_aioresponse.get(url, status=200, payload={"id": "retry", "puuid": "retry", "profileIconId": 1, "revisionDate": 1, "summonerLevel": 30})
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        await client.get_summoner_by_puuid("retry")
        assert mock_sleep.called
    await client.close()


@pytest.mark.asyncio
async def test_session_not_initialized_error(client: NexarClient) -> None:
    with patch.object(client, "_ensure_session"):
        client._session = None
        with pytest.raises(RuntimeError, match="Client session not initialized"):
            await client.get_summoner_by_puuid("test")
    client._session = None


@pytest.mark.asyncio
async def test_unknown_error_message(client: NexarClient, mock_aioresponse: MagicMock) -> None:
    mock_aioresponse.get(
        "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/fail",
        status=500,
        payload={},
    )
    with pytest.raises(RiotAPIError, match="Unknown error"):
        await client.get_summoner_by_puuid("fail")
    await client.close()


@pytest.mark.asyncio
async def test_max_retries_exceeded(client: NexarClient, mock_aioresponse: MagicMock) -> None:
    url = "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/retry_fail"
    for _ in range(6):
        mock_aioresponse.get(url, status=429, headers={"Retry-After": "0.1"}, payload={"status": {"message": "Rate limit", "status_code": 429}})
    with patch("asyncio.sleep", new_callable=AsyncMock), pytest.raises(RateLimitError, match="Max retries .5. exceeded"):
        await client.get_summoner_by_puuid("retry_fail")
    await client.close()


@pytest.mark.asyncio
async def test_debug_print_response_with_params(client: NexarClient, mock_aioresponse: MagicMock, capsys: pytest.CaptureFixture) -> None:
    with patch.dict(os.environ, {"NEXAR_DEBUG_RESPONSES": "1"}):
        mock_aioresponse.get(
            re.compile(r"^https://americas\.api\.riotgames\.com/lol/match/v5/matches/by-puuid/test/ids.*$"),
            payload=[],
        )
        await client.get_match_ids_by_puuid("test", start=10, count=5)
        captured = capsys.readouterr()
        assert "Params:" in captured.out
    await client.close()
