"""Tests for client functionality."""

from typing import TYPE_CHECKING

import pytest

from nexar import BatchError, NexarClient, NotFoundError, Region, RiotAccount
from nexar.cache import NO_CACHE_CONFIG
from tests.helpers import register_exact_url

if TYPE_CHECKING:
    from aioresponses import aioresponses


class TestNexarClient:
    """Test the main NexarClient class."""

    @pytest.mark.slow
    async def test_not_found_error(self, real_client: NexarClient) -> None:
        """The only live 404 contract: a missing riot id raises NotFoundError with its status."""
        with pytest.raises(NotFoundError) as exc_info:
            await real_client.get_riot_account("NonExistentPlayer999", "FAKE")

        assert exc_info.value.status_code == 404

    async def test_get_riot_account_routes_to_regions_own_cluster(
        self,
        mock_aioresponse: "aioresponses",
    ) -> None:
        """An EUW1 account lookup hits the european routing cluster, not the default americas one."""
        register_exact_url(
            mock_aioresponse,
            "https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/bexli/bex",
            {"puuid": "p1", "gameName": "bexli", "tagLine": "bex"},
        )
        client = NexarClient(riot_api_key="key", default_region=Region.NA1, cache_config=NO_CACHE_CONFIG)
        try:
            account = await client.get_riot_account("bexli", "bex", region=Region.EUW1)

            assert account == RiotAccount(puuid="p1", game_name="bexli", tag_line="bex")
        finally:
            await client.close()

    async def test_get_players_with_invalid_riot_id(self, client: NexarClient) -> None:
        """Test get_players with invalid riot ID format."""
        invalid_riot_ids = ["bexli#bex", "invalid_format"]

        with pytest.raises(BatchError) as exc_info:
            await client.get_players(invalid_riot_ids)

        assert "Invalid Riot ID format" in str(exc_info.value)
        assert len(exc_info.value.errors) == 1
        assert exc_info.value.errors[0][0] == "invalid_format"

    @pytest.mark.parametrize(
        ("riot_ids", "expected_count"),
        [
            ([], 0),
            (["bexli#bex"], 1),
            (["bexli#bex", "bexli#bex"], 2),
        ],
        ids=["empty", "one", "two"],
    )
    async def test_get_players_success(self, client: NexarClient, riot_ids: list[str], expected_count: int) -> None:
        players = await client.get_players(riot_ids)

        assert isinstance(players, list)
        assert len(players) == expected_count
        for player in players:
            assert player.game_name == "bexli"
            assert player.tag_line == "bex"
            assert player.riot_account.puuid is not None
