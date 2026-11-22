"""Tests for NexarClient using aioresponses."""

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp_client_cache.session import CachedSession
from aioresponses import aioresponses

from nexar import NexarClient
from nexar.cache import NO_CACHE_CONFIG, CacheConfig
from nexar.enums import Region
from nexar.exceptions import ForbiddenError, NotFoundError, RiotAPIError, UnauthorizedError
from tests.helpers import match_response_payload

if TYPE_CHECKING:
    from nexar.models import Player, Summoner


@pytest.fixture
async def fresh_client(tmp_path: Path) -> AsyncGenerator[NexarClient]:
    """Client with a sqlite cache confined to tmp_path — never ~/.nexar/.

    The session closes after each test, red or green: an unclosed client
    leaves background threads alive and a red run hangs after its summary.
    """
    config = CacheConfig(backend="sqlite", cache_dir=tmp_path)
    client = NexarClient(riot_api_key="test-api-key", default_region=Region.NA1, cache_config=config)
    yield client
    await client.close()


@pytest.fixture
async def stats_client() -> AsyncGenerator[NexarClient]:
    """Uncached client whose session is always closed, even when a test fails."""
    client = NexarClient(riot_api_key="test-api-key", default_region=Region.NA1, cache_config=NO_CACHE_CONFIG)
    yield client
    await client.close()


@pytest.fixture
async def memory_client() -> AsyncGenerator[NexarClient]:
    """In-memory cached client whose session is always closed, even when a test fails."""
    config = CacheConfig(enabled=True, backend="memory", expire_after=60)
    client = NexarClient(riot_api_key="key", default_region=Region.NA1, cache_config=config)
    yield client
    await client.close()


@pytest.mark.asyncio
async def test_get_summoner_by_puuid(fresh_client: NexarClient, mock_aioresponse: aioresponses) -> None:
    mock_aioresponse.get(
        "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/789",
        payload={
            "id": "123",
            "accountId": "456",
            "puuid": "789",
            "name": "TestUser",
            "profileIconId": 1,
            "revisionDate": 123456789,
            "summonerLevel": 30,
        },
    )
    summoner: Summoner = await fresh_client.get_summoner_by_puuid("789")
    assert summoner.summoner_id == "123"
    assert summoner.puuid == "789"
    await fresh_client.close()


@pytest.mark.asyncio
async def test_404_counts_as_error_in_call_stats(stats_client: NexarClient, mock_aioresponse: aioresponses) -> None:
    """A 404 is a non-retryable error and must show up in get_api_call_stats."""
    mock_aioresponse.get(
        "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/UnknownUser",
        status=404,
        payload={"status": {"message": "Not Found", "status_code": 404}},
    )

    with pytest.raises(NotFoundError):
        await stats_client.get_summoner_by_puuid("UnknownUser")

    assert stats_client.get_api_call_stats().errors == 1


@pytest.mark.parametrize(
    ("status", "expected_error"),
    [(401, UnauthorizedError), (403, ForbiddenError)],
)
@pytest.mark.asyncio
async def test_unauthorized_and_forbidden_count_as_errors(
    stats_client: NexarClient,
    mock_aioresponse: aioresponses,
    status: int,
    expected_error: type[RiotAPIError],
) -> None:
    """Auth failures are non-retryable errors and must be counted."""
    mock_aioresponse.get(
        "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/test/tag",
        status=status,
        payload={"status": {"message": "auth failure", "status_code": status}},
    )

    with pytest.raises(expected_error):
        await stats_client.get_riot_account("test", "tag")

    assert stats_client.get_api_call_stats().errors == 1


@pytest.mark.asyncio
async def test_print_api_call_summary_writes_to_stdout(
    stats_client: NexarClient,
    mock_aioresponse: aioresponses,
    capsys: pytest.CaptureFixture,
) -> None:
    """The summary is a print to stdout, not an INFO log: visible with zero logging config.

    Pre-fix, a script with no logging configuration (the default) saw nothing
    from a method named print_api_call_summary.
    """
    stats_client.print_api_call_summary()
    assert "No API calls made yet." in capsys.readouterr().out

    mock_aioresponse.get(
        "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/789",
        payload={
            "id": "123",
            "accountId": "456",
            "puuid": "789",
            "name": "TestUser",
            "profileIconId": 1,
            "revisionDate": 123456789,
            "summonerLevel": 30,
        },
    )
    await stats_client.get_summoner_by_puuid("789")

    stats_client.print_api_call_summary()
    out = capsys.readouterr().out
    assert "API Stats: 1 calls total, 1 fresh, 0 cached (0.0% cache hit rate), 0 retries, 0 errors" in out


@pytest.mark.asyncio
async def test_cache_info_empty(fresh_client: NexarClient) -> None:
    """An enabled cache wires a CachedSession and reports zero rows before any call."""
    await fresh_client._ensure_session()
    assert isinstance(fresh_client._session, CachedSession)
    info = await fresh_client.get_cache_info()
    assert info.enabled is True
    assert info.cached_responses == 0
    await fresh_client.close()


@pytest.mark.asyncio
async def test_cache_hit_serves_stored_row_without_wire(
    memory_client: NexarClient, mock_aioresponse: aioresponses
) -> None:
    """A stored 200 row is served by the manual read path, counted as a cache hit, wire untouched."""
    await memory_client._ensure_session()
    session = memory_client._session
    assert isinstance(session, CachedSession)

    url = "https://americas.api.riotgames.com/lol/match/v5/matches/M_123"
    mock_aioresponse.get(url, payload=match_response_payload("M_123"))
    response = await session.get(url)
    # aioresponses fabricates a lowercase method; fix it so the save is accepted
    response.method = "GET"
    await session.cache.save_response(response)

    match = await memory_client.get_match("M_123")

    assert match.metadata.match_id == "M_123"
    stats = memory_client.get_api_call_stats()
    assert stats.cache_hits == 1
    assert stats.fresh_calls == 0


@pytest.mark.asyncio
async def test_cache_row_with_empty_body_is_a_miss(memory_client: NexarClient, mock_aioresponse: aioresponses) -> None:
    """A stored 200 row with an empty body decodes to None: the row is dropped and the wire serves."""
    await memory_client._ensure_session()
    session = memory_client._session
    assert isinstance(session, CachedSession)

    url = "https://americas.api.riotgames.com/lol/match/v5/matches/M_456"
    mock_aioresponse.get(url, body=b"")
    response = await session.get(url)
    response.method = "GET"
    await session.cache.save_response(response)

    mock_aioresponse.get(url, payload=match_response_payload("M_456"))
    match = await memory_client.get_match("M_456")

    assert match.metadata.match_id == "M_456"
    stats = memory_client.get_api_call_stats()
    assert stats.cache_hits == 0
    assert stats.fresh_calls == 1
    # The junk row is gone; aioresponses' lowercase method blocks the library's own write.
    assert await session.cache.responses.size() == 0


@pytest.mark.asyncio
async def test_clear_cache_populated_to_empty(memory_client: NexarClient, mock_aioresponse: aioresponses) -> None:
    """clear_cache drops stored rows: one row before, zero after."""
    await memory_client._ensure_session()
    session = memory_client._session
    assert isinstance(session, CachedSession)

    url = "https://na1.api.riotgames.com/lol/test/clear"
    mock_aioresponse.get(url, payload={"ok": True})
    response = await session.get(url)
    response.method = "GET"
    await session.cache.save_response(response)

    assert await session.cache.responses.size() == 1

    await memory_client.clear_cache()

    assert await session.cache.responses.size() == 0
