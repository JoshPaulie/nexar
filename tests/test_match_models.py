"""Tests for match models."""

import dataclasses
from typing import TYPE_CHECKING

import pytest

from nexar import NexarClient
from nexar.cache import NO_CACHE_CONFIG
from nexar.enums import Region
from nexar.models import Challenges, Objective, Objectives
from tests.helpers import create_test_participant, register_exact_url

if TYPE_CHECKING:
    from aioresponses import aioresponses

    from nexar.client import NexarClient as NexarClientT


class TestMatchModels:
    """Test match-related models."""

    @pytest.mark.slow
    async def test_match_from_api_response(self, real_client: "NexarClientT") -> None:
        """Live canary: a fetched 5v5 match parses with a full participant list."""
        player = await real_client.get_player(game_name="bexli", tag_line="bex")
        matches = await player.get_matches(count=1)

        assert matches
        match = matches[0]
        assert len(match.info.participants) == 10  # Standard 5v5 match
        assert match.metadata.match_id

    def test_challenges_creation(self) -> None:
        """Test Challenges creation from API response."""
        challenges_data = {
            "kda": 6.5,
            "killParticipation": 0.65,
            "damagePerMinute": 833.33,
            "goldPerMinute": 500.0,
            "visionScorePerMinute": 1.5,
        }

        challenges = Challenges.from_api_response(challenges_data)

        assert challenges.kda == 6.5
        assert challenges.kill_participation == 0.65
        assert challenges.damage_per_minute == 833.33
        assert challenges.gold_per_minute == 500.0
        assert challenges.vision_score_per_minute == 1.5

    def test_field_map_covers_every_challenge_field(self) -> None:
        """_FIELD_MAP and the Challenges fields cannot drift apart (P13: a deleted entry fails silently)."""
        field_names = {field.name for field in dataclasses.fields(Challenges)}
        mapped_names = set(Challenges._FIELD_MAP.values())

        assert len(mapped_names) == len(Challenges._FIELD_MAP)  # no duplicate targets
        assert mapped_names == field_names

    def test_objectives_creation(self) -> None:
        """A full recorded objectives payload parses to its exact value, horde present with zero."""
        objectives = Objectives.from_api_response(
            {
                "baron": {"first": True, "kills": 1},
                "champion": {"first": True, "kills": 20},
                "dragon": {"first": True, "kills": 3},
                "horde": {"first": False, "kills": 0},
                "inhibitor": {"first": True, "kills": 2},
                "riftHerald": {"first": True, "kills": 1},
                "tower": {"first": True, "kills": 8},
            },
        )

        assert objectives == Objectives(
            baron=Objective(first=True, kills=1),
            champion=Objective(first=True, kills=20),
            dragon=Objective(first=True, kills=3),
            inhibitor=Objective(first=True, kills=2),
            rift_herald=Objective(first=True, kills=1),
            tower=Objective(first=True, kills=8),
            horde=Objective(first=False, kills=0),
        )

    async def test_get_player_resolves_participant_puuid(
        self,
        mock_aioresponse: "aioresponses",
    ) -> None:
        """Participant.get_player looks up the participant's own puuid (exact URL registered)."""
        participant = create_test_participant(puuid="test-puuid-123")
        register_exact_url(
            mock_aioresponse,
            "https://americas.api.riotgames.com/riot/account/v1/accounts/by-puuid/test-puuid-123",
            {"puuid": "test-puuid-123", "gameName": "bexli", "tagLine": "bex"},
        )
        client = NexarClient(riot_api_key="key", default_region=Region.NA1, cache_config=NO_CACHE_CONFIG)
        try:
            player = await participant.get_player(client)

            assert player.puuid == "test-puuid-123"
            assert player.game_name == "bexli"
            assert player.tag_line == "bex"
        finally:
            await client.close()

    @pytest.mark.slow
    async def test_get_player_with_real_client(self, real_client: "NexarClientT") -> None:
        """Integration test: get_player() returns a real Player."""
        player = await real_client.get_player(game_name="bexli", tag_line="bex")
        matches = await player.get_matches(count=1)

        assert matches
        participant = matches[0].participants.by_puuid(player.puuid)
        assert participant is not None

        player_from_participant = await participant.get_player(real_client)

        # Both Players should reference the same Riot account (same PUUID)
        assert player_from_participant.riot_account.puuid == player.riot_account.puuid
