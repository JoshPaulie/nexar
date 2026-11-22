"""NexarClient behavior tests, grouped by contract.

Sections: parameter wiring (match-ids), batch fetches, session and cache
lifecycle, error mapping, 429 retry pacing, 5xx retry pacing, debug output.
"""

import asyncio
import os
import re
import sqlite3
import time
from collections.abc import AsyncGenerator, Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from aiohttp_client_cache.session import CachedSession

from nexar.cache import NO_CACHE_CONFIG, CacheConfig
from nexar.client import NexarClient
from nexar.client_plumbing import DEFAULT_RETRY_AFTER_SECONDS
from nexar.enums import MatchType, Queue, Region
from nexar.exceptions import RateLimitError, RiotAPIError
from tests.helpers import match_response_payload

if TYPE_CHECKING:
    from aioresponses import aioresponses


@pytest.fixture
async def client(tmp_path: Path) -> AsyncGenerator[NexarClient]:
    """Client whose cache lives in tmp_path, never in the shared ~/.nexar/ store.

    The session closes after each test, red or green: an unclosed client
    leaves background threads alive and a red run hangs after its summary.
    """
    config = CacheConfig(backend="sqlite", cache_dir=tmp_path)
    nexar_client = NexarClient(riot_api_key="test-key", default_region=Region.NA1, cache_config=config)
    yield nexar_client
    await nexar_client.close()


# ---------------------------------------------------------------------------
# Parameter wiring
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_match_ids_all_params(client: NexarClient, mock_aioresponse: MagicMock) -> None:
    """The exact-URL pin: every documented parameter lands in the query string."""
    mock_aioresponse.get(
        "https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/test-puuid/ids"
        "?count=5&endTime=1600000000&queue=420&start=10&startTime=1500000000&type=ranked",
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
    assert match_ids == ["NA1_1"]
    await client.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("start_time", "end_time"),
    [
        (1500000000, 1600000000),
        (datetime.fromtimestamp(1500000000, tz=UTC), datetime.fromtimestamp(1600000000, tz=UTC)),
        (
            datetime.fromtimestamp(1500000000, tz=UTC).replace(tzinfo=None),
            datetime.fromtimestamp(1600000000, tz=UTC).replace(tzinfo=None),
        ),
    ],
    ids=["int-epochs", "aware-datetimes", "naive-datetimes"],
)
async def test_get_match_ids_times_encode_as_epoch_query(
    client: NexarClient,
    mock_aioresponse: MagicMock,
    start_time: int | datetime,
    end_time: int | datetime,
) -> None:
    """Int epochs and datetimes (aware or naive) all encode as the same epoch query."""
    mock_aioresponse.get(
        "https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/test-puuid/ids"
        "?endTime=1600000000&startTime=1500000000",
        payload=["NA1_1", "NA1_2"],
    )
    match_ids = await client.get_match_ids_by_puuid("test-puuid", start_time=start_time, end_time=end_time)
    assert match_ids == ["NA1_1", "NA1_2"]
    await client.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"count": 101}, "count must be between 0 and 100"),
        ({"count": -1}, "count must be between 0 and 100"),
        ({"start": -1}, "start must be non-negative"),
    ],
    ids=["count-too-high", "count-negative", "start-negative"],
)
async def test_get_match_ids_validation_error(client: NexarClient, kwargs: dict, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        await client.get_match_ids_by_puuid("test-puuid", **kwargs)
    await client.close()


# ---------------------------------------------------------------------------
# Batch fetches and single-resource parsing
# ---------------------------------------------------------------------------


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
async def test_get_players(client: NexarClient, mock_aioresponse: MagicMock) -> None:
    """The strongest get_players row: distinct ids resolve to distinct payloads."""
    mock_aioresponse.get(
        "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/Player1/TAG",
        payload={"puuid": "p1", "gameName": "Player1", "tagLine": "TAG"},
    )
    mock_aioresponse.get(
        "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/Player2/TAG",
        payload={"puuid": "p2", "gameName": "Player2", "tagLine": "TAG"},
    )
    players = await client.get_players(["Player1#TAG", "Player2#TAG"])
    assert len(players) == 2
    assert players[0].game_name == "Player1"
    assert players[1].game_name == "Player2"
    await client.close()


@pytest.mark.asyncio
async def test_get_match(client: NexarClient, mock_aioresponse: MagicMock) -> None:
    response_data = match_response_payload("NA1_12345")
    mock_aioresponse.get(
        "https://americas.api.riotgames.com/lol/match/v5/matches/NA1_12345",
        payload=response_data,
    )
    match = await client.get_match("NA1_12345")
    assert match.metadata.match_id == "NA1_12345"
    await client.close()


@pytest.mark.asyncio
async def test_api_key_rides_the_wire_as_the_riot_token_header(
    client: NexarClient,
    mock_aioresponse: "aioresponses",
) -> None:
    """Every wire request carries the caller's key as X-Riot-Token.

    No other row inspects outbound headers, so a dropped token would pass the
    whole mocked suite and only fail live, as 401s on every call.
    """
    sent_headers: dict[str, str] = {}

    def record_headers(_url: object, *, headers: dict[str, str], **_kwargs: object) -> None:
        sent_headers.update(headers)

    url = "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/token_check"
    mock_aioresponse.get(
        url,
        payload={"id": "t", "puuid": "token_check", "profileIconId": 1, "revisionDate": 1, "summonerLevel": 30},
        callback=record_headers,
    )

    await client.get_summoner_by_puuid("token_check")

    assert sent_headers["X-Riot-Token"] == "test-key"
    await client.close()


# ---------------------------------------------------------------------------
# Session and cache lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_context_manager(client: NexarClient) -> None:
    async with client as c:
        assert c is client
        assert c._session is not None
        assert not c._session.closed
    assert client._session is not None
    assert client._session.closed


@pytest.mark.asyncio
async def test_ensure_session_no_cache() -> None:
    config = CacheConfig(enabled=False)
    client = NexarClient(riot_api_key="key", cache_config=config, default_region=Region.NA1)
    try:
        await client._ensure_session()
        assert not isinstance(client._session, CachedSession)
        assert isinstance(client._session, aiohttp.ClientSession)
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_get_cache_info_details(client: NexarClient) -> None:
    """The row count reads the storage's size(); cache_size was never a real key."""
    await client._ensure_session()
    session = client._session
    assert isinstance(session, CachedSession)
    # sqlite tables exist only after the first awaited op (documented in SKILL).
    await session.cache.get_response("warmup")
    await session.cache.responses.write("row-1", "v1")
    await session.cache.responses.write("row-2", "v2")
    info = await client.get_cache_info()
    assert info["cached_responses"] == 2
    assert info["backend"] == "sqlite"
    assert "cache_size" not in info
    await client.close()


@pytest.mark.asyncio
async def test_cache_info_exception(client: NexarClient) -> None:
    """An uncountable storage reports 0 instead of raising."""
    await client._ensure_session()
    mock_cache = MagicMock()
    mock_cache.responses.size = AsyncMock(side_effect=sqlite3.OperationalError("database is locked"))
    mock_cache._close_if_enabled = AsyncMock()
    assert client._session is not None
    client._session.cache = mock_cache
    info = await client.get_cache_info()
    assert info["cached_responses"] == 0
    await client.close()


# ---------------------------------------------------------------------------
# Error mapping
# ---------------------------------------------------------------------------


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
async def test_resolve_region_error() -> None:
    """A client with no default region refuses to guess on a regionless call."""
    client = NexarClient(riot_api_key="key", cache_config=NO_CACHE_CONFIG)
    try:
        with pytest.raises(ValueError, match="A region must be provided"):
            await client.get_summoner_by_puuid("test")
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_binary_400_body_raises_typed_error(client: NexarClient, mock_aioresponse: MagicMock) -> None:
    """An undecodable error body maps to a typed RiotAPIError, not UnicodeDecodeError."""
    url = "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/binary_fail"
    mock_aioresponse.get(url, status=400, body=b"\xff\xfe\x00binary\x01\x02")

    with pytest.raises(RiotAPIError) as excinfo:
        await client.get_summoner_by_puuid("binary_fail")

    # Replacement characters stand in for the undecodable bytes; the
    # decodable tail survives in the bounded preview.
    assert "binary" in str(excinfo.value)
    stats = client.get_api_call_stats()
    assert stats.errors == 1
    await client.close()


# ---------------------------------------------------------------------------
# 429 retry pacing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_retry_logic_429(client: NexarClient, mock_aioresponse: MagicMock) -> None:
    url = "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/retry"
    mock_aioresponse.get(
        url,
        status=429,
        headers={"Retry-After": "0.1"},
        payload={"status": {"message": "Rate limit", "status_code": 429}},
    )
    mock_aioresponse.get(
        url,
        status=200,
        payload={"id": "retry", "puuid": "retry", "profileIconId": 1, "revisionDate": 1, "summonerLevel": 30},
    )
    t0 = time.monotonic()
    summoner = await client.get_summoner_by_puuid("retry")
    elapsed = time.monotonic() - t0
    assert summoner.puuid == "retry"
    # The Retry-After block must be honored once, in real time.
    assert 0.05 <= elapsed <= 1.0, f"expected ~0.1s wait, got {elapsed:.2f}s"
    await client.close()


@pytest.mark.asyncio
async def test_max_retries_exceeded(client: NexarClient, mock_aioresponse: MagicMock) -> None:
    url = "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/retry_fail"
    for _ in range(6):
        mock_aioresponse.get(
            url,
            status=429,
            headers={"Retry-After": "0.1"},
            payload={"status": {"message": "Rate limit", "status_code": 429}},
        )
    t0 = time.monotonic()
    with pytest.raises(RateLimitError, match=r"Max attempts .5. exceeded"):
        await client.get_summoner_by_puuid("retry_fail")
    elapsed = time.monotonic() - t0
    # 5 blocked retries at 0.1s each must actually wait.
    assert elapsed >= 0.4, f"retries did not honor Retry-After: {elapsed:.2f}s"
    await client.close()


@pytest.mark.parametrize(
    "header",
    [None, "not-a-number", "nan", "inf"],
    ids=["missing", "non-numeric", "nan", "infinite"],
)
def test_parse_retry_after_falls_back_to_default(header: str | None) -> None:
    """A missing, garbled, or non-finite Retry-After all block for the conservative default.

    ``block(region, nan)`` would never block at all, so the parser clamps the
    non-finite spellings to the default instead of passing them through. The
    5s value is published behavior (CHANGELOG: the conservative 5s default),
    so it is pinned literally, not just by name.
    """
    assert NexarClient._parse_retry_after(header) == DEFAULT_RETRY_AFTER_SECONDS == 5.0


# ---------------------------------------------------------------------------
# 5xx retry pacing
# ---------------------------------------------------------------------------

# A Cloudflare-style error page, like the live Riot 502 that surfaced whole
# in a RiotAPIError during the dogfood audit: HTML, doctype first, well past
# 200 characters.
CLOUDFLARE_ERROR_PAGE = (
    "<!DOCTYPE html>\n"
    '<html lang="en-US">\n<head><title>502 Bad Gateway</title></head>\n'
    "<body>Cloudflare edge error page boilerplate.\n</body>\n</html>\n" * 20
)


@pytest.mark.asyncio
async def test_503_then_200_succeeds_after_one_retry(client: NexarClient, mock_aioresponse: MagicMock) -> None:
    """A Cloudflare-style 503 is retried with a per-call backoff, then the real row lands."""
    url = "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/blip"
    mock_aioresponse.get(url, status=503, body=CLOUDFLARE_ERROR_PAGE)
    mock_aioresponse.get(
        url,
        status=200,
        payload={"id": "b", "puuid": "blip", "profileIconId": 1, "revisionDate": 1, "summonerLevel": 30},
    )
    t0 = time.monotonic()
    summoner = await client.get_summoner_by_puuid("blip")
    elapsed = time.monotonic() - t0
    assert summoner.puuid == "blip"
    stats = client.get_api_call_stats()
    assert stats.retries == 1
    assert stats.fresh_calls == 1
    # The first backoff (0.5s base) actually sleeps, in real time.
    assert elapsed >= 0.4, f"expected ~0.5s backoff, got {elapsed:.2f}s"
    await client.close()


@pytest.mark.asyncio
async def test_binary_503_body_still_retries(client: NexarClient, mock_aioresponse: MagicMock) -> None:
    """An undecodable 5xx body does not escape the retry machinery untyped.

    ``response.text()`` raises UnicodeDecodeError on garbled bytes; without
    the decode-safe read the raw exception surfaced with no retry, no typed
    error, and no stats.
    """
    url = "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/binary_blip"
    mock_aioresponse.get(url, status=503, body=b"\xff\xfe\x00binary\x01\x02")
    mock_aioresponse.get(
        url,
        status=200,
        payload={"id": "b", "puuid": "binary_blip", "profileIconId": 1, "revisionDate": 1, "summonerLevel": 30},
    )
    summoner = await client.get_summoner_by_puuid("binary_blip")
    assert summoner.puuid == "binary_blip"
    stats = client.get_api_call_stats()
    assert stats.retries == 1
    await client.close()


@pytest.mark.asyncio
async def test_502_exhaustion_retries_then_raises_typed_error_without_the_html_page(
    client: NexarClient,
    mock_aioresponse: MagicMock,
) -> None:
    """Five 502s: retries counted in CallStats, region ledger never blocked, typed error.

    The final error carries a bounded, tag-stripped preview of the HTML
    page, not the page — the dogfood audit measured a live Riot 502 landing
    whole in the exception text.
    """
    url = "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/server_error"
    for _ in range(5):
        mock_aioresponse.get(url, status=502, body=CLOUDFLARE_ERROR_PAGE)

    sleeps: list[float] = []
    real_sleep = asyncio.sleep

    async def record_and_skip(seconds: float) -> None:
        sleeps.append(seconds)
        await real_sleep(0)

    with patch.object(asyncio, "sleep", record_and_skip), pytest.raises(RiotAPIError) as excinfo:
        await client.get_summoner_by_puuid("server_error")

    error_text = str(excinfo.value)
    assert "<!DOCTYPE" not in error_text
    assert "502 Bad Gateway" in error_text
    assert len(error_text) < 500
    stats = client.get_api_call_stats()
    assert stats.retries == 4
    assert stats.errors == 1
    # Per-call backoff doubling from the 0.5s base; the region ledger is never
    # blocked, so no pacing sleeps appear between the backoffs.
    assert sleeps == [0.5, 1.0, 2.0, 4.0]
    await client.close()


# ---------------------------------------------------------------------------
# Transport-error retry pacing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure",
    [aiohttp.ClientConnectionError("Connection refused"), TimeoutError()],
    ids=["connection-error", "timeout"],
)
async def test_transport_error_exhaustion_retries_then_raises_typed_error(
    client: NexarClient,
    mock_aioresponse: "aioresponses",
    failure: Exception,
) -> None:
    """Five transport failures retry on the doubling ladder, then raise a typed error.

    Mirrors the 502 exhaustion row: retries counted in CallStats, no pacing
    sleeps between backoffs, and the raised error is RiotAPIError, never the
    raw transport exception.
    """
    url = "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/transport_down"
    for _ in range(5):
        mock_aioresponse.get(url, exception=failure)

    sleeps: list[float] = []
    real_sleep = asyncio.sleep

    async def record_and_skip(seconds: float) -> None:
        sleeps.append(seconds)
        await real_sleep(0)

    with (
        patch.object(asyncio, "sleep", record_and_skip),
        pytest.raises(RiotAPIError, match="Request failed after 5 attempts"),
    ):
        await client.get_summoner_by_puuid("transport_down")

    stats = client.get_api_call_stats()
    assert stats.retries == 4
    assert stats.errors == 0
    # The transport ladder doubles from a 1s base; the region ledger is never
    # blocked, so no pacing sleeps join the backoffs.
    assert sleeps == [1, 2, 4, 8]
    await client.close()


# ---------------------------------------------------------------------------
# Debug output
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("make_request", "expected_snippet"),
    [
        (lambda c: c.get_summoner_by_puuid("test"), "DEBUG: API Response"),
        (lambda c: c.get_match_ids_by_puuid("test", start=10, count=5), "Params:"),
    ],
    ids=["no-params", "with-params"],
)
async def test_debug_print_response(
    client: NexarClient,
    mock_aioresponse: "aioresponses",
    capsys: pytest.CaptureFixture,
    make_request: Callable[[NexarClient], Awaitable[object]],
    expected_snippet: str,
) -> None:
    """NEXAR_DEBUG_RESPONSES=1 prints the response block, and the params line when a call has them."""
    with patch.dict(os.environ, {"NEXAR_DEBUG_RESPONSES": "1"}):
        mock_aioresponse.get(
            "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/test",
            payload={
                "id": "test",
                "puuid": "test-puuid",
                "profileIconId": 1,
                "revisionDate": 123456789,
                "summonerLevel": 100,
            },
        )
        mock_aioresponse.get(
            re.compile(r"^https://americas\.api\.riotgames\.com/lol/match/v5/matches/by-puuid/test/ids.*$"),
            payload=[],
        )
        result = await make_request(client)
        assert result is not None
        captured = capsys.readouterr()
        assert expected_snippet in captured.out
    await client.close()
