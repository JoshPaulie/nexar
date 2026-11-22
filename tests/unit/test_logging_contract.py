"""The package logging contract: silent unless the application opts in.

A library logger with no handler reaches the logging module's last-resort
handler, which prints to stderr at WARNING and above — pre-fix, a handled
404 or an unknown queue string printed uninvited with zero configuration.
The package attaches a NullHandler to ``nexar`` (children inherit the
chain) so records die silently unless the app configures logging, and the
expected-noise records (handled 4xx, unknown-queue fallbacks) log at DEBUG
while the typed exceptions keep carrying everything the dropped lines did.
"""

import logging
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import pytest

from nexar.cache import NO_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import Queue, Region
from nexar.exceptions import NotFoundError
from nexar.models import LeagueEntry

if TYPE_CHECKING:
    from aioresponses import aioresponses

NOT_FOUND_URL = "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/ghost"
NOT_FOUND_PAYLOAD = {"status": {"message": "No summoner data found.", "status_code": 404}}


@pytest.fixture
async def stats_client() -> AsyncGenerator[NexarClient]:
    """Uncached client whose session is always closed, even when a test fails."""
    client = NexarClient(riot_api_key="test-api-key", default_region=Region.NA1, cache_config=NO_CACHE_CONFIG)
    yield client
    await client.close()


@pytest.mark.asyncio
async def test_handled_404_writes_nothing_to_stderr_without_logging_config(
    stats_client: NexarClient,
    mock_aioresponse: "aioresponses",
    capsys: pytest.CaptureFixture,
) -> None:
    """No logging configured anywhere: a handled 404 leaves stderr empty.

    conftest's ``basicConfig`` is the test harness's own configuration and
    is cleared for the duration of this call, simulating an application
    that never touched logging.
    """
    mock_aioresponse.get(NOT_FOUND_URL, status=404, payload=NOT_FOUND_PAYLOAD)

    root = logging.getLogger()
    saved_handlers = root.handlers
    root.handlers = []
    try:
        with pytest.raises(NotFoundError) as excinfo:
            await stats_client.get_summoner_by_puuid("ghost")
    finally:
        root.handlers = saved_handlers

    captured = capsys.readouterr()
    assert captured.err == ""
    # The typed exception carries everything the dropped log line did.
    assert "No summoner data found." in str(excinfo.value)


@pytest.mark.asyncio
async def test_expected_4xx_logs_at_debug_not_warning(
    stats_client: NexarClient,
    mock_aioresponse: "aioresponses",
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A handled 404 is routine control flow: its log record is DEBUG, never WARNING."""
    caplog.set_level(logging.DEBUG, logger="nexar")
    mock_aioresponse.get(NOT_FOUND_URL, status=404, payload=NOT_FOUND_PAYLOAD)

    with pytest.raises(NotFoundError):
        await stats_client.get_summoner_by_puuid("ghost")

    records = [r for r in caplog.records if r.name == "nexar" and "API error" in r.getMessage()]
    assert records
    assert all(r.levelname == "DEBUG" for r in records)


def test_unknown_queue_id_logs_at_debug_not_warning(caplog: pytest.LogCaptureFixture) -> None:
    """An unknown queue ID degrades to the UNKNOWN sentinel at DEBUG, quietly."""
    caplog.set_level(logging.DEBUG, logger="nexar")

    assert Queue(1750) is Queue.UNKNOWN

    records = [r for r in caplog.records if r.name == "nexar" and "Unknown queue ID" in r.getMessage()]
    assert records
    assert all(r.levelname == "DEBUG" for r in records)


def test_unknown_queue_type_logs_at_debug_not_warning(caplog: pytest.LogCaptureFixture) -> None:
    """An unknown queue string in a league payload degrades at DEBUG, quietly."""
    caplog.set_level(logging.DEBUG, logger="nexar")

    entry = LeagueEntry.from_api_response({"queueType": "RANKED_NEW_THING", "puuid": "p", "tier": "GOLD"})

    assert entry.queue_type is Queue.UNKNOWN
    assert entry.queue_type_raw == "RANKED_NEW_THING"
    records = [r for r in caplog.records if r.name == "nexar" and "Unknown queue type" in r.getMessage()]
    assert records
    assert all(r.levelname == "DEBUG" for r in records)
