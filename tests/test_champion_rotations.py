"""Tests for champion rotations (champion-v3)."""

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio

from nexar.cache import NO_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import Region
from nexar.models import ChampionRotations
from tests.helpers import register_exact_url

if TYPE_CHECKING:
    from aioresponses import aioresponses


def rotations_payload() -> dict[str, list[int]]:
    """Champion rotation in the recorded live shape (2026-11-21 NA1, trimmed).

    Riot's DTO spells the two pools ``sr`` and ``newplayer`` — the model mirrors
    those wire keys exactly.
    """
    return {
        "sr": [29, 30, 40, 43, 62, 75, 103, 110, 112, 115],
        "newplayer": [17, 18, 33, 37, 51, 54, 80, 82],
    }


@pytest_asyncio.fixture
async def fresh_client() -> AsyncGenerator[NexarClient]:
    """Client with no conftest catch-alls, so the exact-URL registration is the only match."""
    client = NexarClient(riot_api_key="test-api-key", default_region=Region.NA1, cache_config=NO_CACHE_CONFIG)
    yield client
    await client.close()


class TestChampionRotationsClient:
    """The rotations op against an exact-URL registration (routing and path pinning)."""

    async def test_get_champion_rotations_parses_recorded_payload(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        register_exact_url(
            mock_aioresponse,
            "https://na1.api.riotgames.com/lol/platform/v3/champion-rotations",
            rotations_payload(),
        )

        rotations = await fresh_client.get_champion_rotations()

        assert rotations == ChampionRotations(
            sr=(29, 30, 40, 43, 62, 75, 103, 110, 112, 115),
            newplayer=(17, 18, 33, 37, 51, 54, 80, 82),
        )


class TestChampionRotationsModels:
    """ChampionRotations parsing."""

    def test_wire_keys_are_preserved(self) -> None:
        rotations = ChampionRotations.from_api_response(rotations_payload())

        assert rotations.sr[0] == 29
        assert rotations.newplayer[0] == 17

    def test_omitted_pools_parse_empty(self) -> None:
        """Riot omits empty values, so a stripped payload parses rather than raising."""
        rotations = ChampionRotations.from_api_response({})

        assert rotations.sr == ()
        assert rotations.newplayer == ()


class TestLiveRotationCanary:
    """Live canary: the rotations op against the real API."""

    @pytest.mark.slow
    async def test_live_rotation_returns_both_pools(self, real_client: NexarClient) -> None:
        rotations = await real_client.get_champion_rotations()

        assert rotations.sr
        assert rotations.newplayer
        assert all(isinstance(champion_id, int) for champion_id in rotations.sr + rotations.newplayer)
