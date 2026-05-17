"""Test configuration and fixtures."""

import asyncio
import json
import logging
import os
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Any, cast

import pytest
import pytest_asyncio
from aioresponses import aioresponses

from nexar import NexarClient
from nexar.cache import NO_CACHE_CONFIG
from nexar.enums import Region

# Configure logging so rate limiter warnings (proactive pacing and 429s) are visible
logging.basicConfig(level=logging.WARNING, format="%(levelname)s [%(name)s] %(message)s")

# Seconds to pause between integration tests to respect Riot API rate limits
INTEGRATION_TEST_PAUSE = 25


def pytest_configure(config: pytest.Config) -> None:
    config.option.maxfail = 1
    config.option.numprocesses = 1


@pytest.fixture(scope="session")
def mock_responses() -> dict[str, Any]:
    mock_file = Path("tests/mock_responses.json")
    return cast("dict[str, Any]", json.loads(mock_file.read_text()))


@pytest.fixture
def riot_api_key() -> str:
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        pytest.skip("RIOT_API_KEY environment variable not set. Source riot-key.sh before running tests.")
    return api_key


@pytest.fixture
def mock_aioresponse() -> Generator[aioresponses]:
    with aioresponses() as m:
        yield m


@pytest_asyncio.fixture
async def client(
    mock_aioresponse: aioresponses,
    mock_responses: dict[str, Any],
) -> AsyncGenerator[NexarClient]:
    import re

    mock_aioresponse.get(
        re.compile(r"https://.*\.api\.riotgames\.com/riot/account/v1/accounts/by-riot-id/.*"),
        payload=mock_responses["riot_account"],
        repeat=True,
    )

    mock_aioresponse.get(
        re.compile(r"https://.*\.api\.riotgames\.com/riot/account/v1/accounts/by-puuid/.*"),
        payload=mock_responses["riot_account"],
        repeat=True,
    )

    mock_aioresponse.get(
        re.compile(r"https://.*\.api\.riotgames\.com/lol/summoner/v4/summoners/by-puuid/.*"),
        payload=mock_responses["summoner"],
        repeat=True,
    )
    mock_aioresponse.get(
        re.compile(r"https://.*\.api\.riotgames\.com/lol/summoner/v4/summoners/by-name/.*"),
        payload=mock_responses["summoner"],
        repeat=True,
    )

    mock_aioresponse.get(
        re.compile(r"https://.*\.api\.riotgames\.com/lol/match/v5/matches/by-puuid/.*/ids.*"),
        payload=mock_responses["match_ids"],
        repeat=True,
    )

    mock_aioresponse.get(
        re.compile(r"https://.*\.api\.riotgames\.com/lol/match/v5/matches/(?!by-puuid).+"),
        payload=mock_responses["match"],
        repeat=True,
    )

    mock_aioresponse.get(
        re.compile(r"https://.*\.api\.riotgames\.com/lol/league/v4/entries/by-summoner/.*"),
        payload=mock_responses["league_entries"],
        repeat=True,
    )
    mock_aioresponse.get(
        re.compile(r"https://.*\.api\.riotgames\.com/lol/league/v4/entries/by-puuid/.*"),
        payload=mock_responses["league_entries"],
        repeat=True,
    )

    nexar_client = NexarClient(
        riot_api_key="test-api-key",
        default_region=Region.NA1,
        cache_config=NO_CACHE_CONFIG,
    )

    yield nexar_client

    await nexar_client.close()


@pytest_asyncio.fixture
async def real_client(riot_api_key: str) -> AsyncGenerator[NexarClient]:
    client = NexarClient(
        riot_api_key=riot_api_key,
        default_region=Region.NA1,
        cache_config=NO_CACHE_CONFIG,
    )
    yield client

    stats = client.get_api_call_stats()
    status = "✓ clean — no rate limits hit" if stats.retries == 0 else f"⚠ {stats.retries} RATE LIMIT RETRIES (429s)"
    logger = logging.getLogger("nexar.test")
    logger.warning(
        "Call stats: %d fresh, %d cached, %d retries, %d errors — %s",
        stats.fresh_calls,
        stats.cache_hits,
        stats.retries,
        stats.errors,
        status,
    )
    await client.close()


@pytest.fixture(autouse=True)
def _pause_between_integration_tests(request: pytest.FixtureRequest) -> None:
    """Pause before each slow (integration) test to respect Riot API rate limits."""
    if "slow" in request.node.keywords:
        asyncio.run(asyncio.sleep(INTEGRATION_TEST_PAUSE))
