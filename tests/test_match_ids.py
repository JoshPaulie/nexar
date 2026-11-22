"""Exact-URL tests for get_match_ids_by_puuid query construction.

Every registration is a literal URL: the request only succeeds when the client
builds the exact query string the case names, so a dropped or mangled parameter
fails the call instead of silently matching a catch-all regex (probe P7).
"""

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import pytest

from nexar import MatchType, NexarClient, Queue
from nexar.cache import NO_CACHE_CONFIG
from nexar.enums import Region
from tests.helpers import register_exact_url

if TYPE_CHECKING:
    from aioresponses import aioresponses

_IDS_URL = "https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/test-puuid/ids"


@pytest.fixture
async def exact_client() -> AsyncGenerator[NexarClient]:
    """Isolated uncached client on literal registrations, closed even when a row fails."""
    client = NexarClient(riot_api_key="test-api-key", default_region=Region.NA1, cache_config=NO_CACHE_CONFIG)
    yield client
    await client.close()


@pytest.mark.parametrize(
    ("kwargs", "query"),
    [
        ({}, ""),
        ({"count": 5}, "?count=5"),
        ({"queue": Queue.ARAM}, "?queue=450"),
        ({"queue": 450}, "?queue=450"),
        ({"match_type": MatchType.NORMAL}, "?type=normal"),
        ({"match_type": "normal"}, "?type=normal"),
        ({"start": 10}, "?start=10"),
    ],
    ids=[
        "no-params",
        "count",
        "queue-enum",
        "queue-raw-int",
        "match-type-enum",
        "match-type-raw-str",
        "start",
    ],
)
async def test_get_match_ids_builds_exact_query(
    exact_client: NexarClient,
    mock_aioresponse: "aioresponses",
    kwargs: dict,
    query: str,
) -> None:
    """Only the exact URL answers, so every parameter must survive the builder."""
    register_exact_url(mock_aioresponse, _IDS_URL + query, ["NA1_1"])

    ids = await exact_client.get_match_ids_by_puuid("test-puuid", **kwargs)

    assert ids == ["NA1_1"]
