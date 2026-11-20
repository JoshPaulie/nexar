"""Tests for domain models."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from nexar.enums import Region
from nexar.models import RiotAccount, Summoner

if TYPE_CHECKING:
    from nexar.client import NexarClient


class TestRiotAccount:
    async def test_from_recorded_payload(self, client: "NexarClient") -> None:
        """Parsing the recorded by-riot-id payload yields its exact values."""
        account = await client.get_riot_account("bexli", "bex")

        assert account == RiotAccount(
            puuid="0wKS4sQQTcA6mAmu_oW5rVhyxmWAXV9hZrraXnDdh8GvelgGWYM5tM7fcHw0kalBVgCl6MxOZe0bLA",
            game_name="bexli",
            tag_line="bex",
        )


class TestSummoner:
    async def test_from_recorded_payload(self, client: "NexarClient") -> None:
        """The recorded by-puuid payload parses to its exact values, including the ms→UTC revision_date."""
        test_puuid = "0wKS4sQQTcA6mAmu_oW5rVhyxmWAXV9hZrraXnDdh8GvelgGWYM5tM7fcHw0kalBVgCl6MxOZe0bLA"
        summoner = await client.get_summoner_by_puuid(test_puuid, region=Region.NA1)

        assert summoner == Summoner(
            summoner_id="tEk0cj7yiDLyM1tNKrIx3xCmnBblr-sync6-PHy-plSS4Mw",
            puuid=test_puuid,
            profile_icon_id=5435,
            revision_date=datetime.fromtimestamp(1751822528, tz=UTC),
            summoner_level=511,
        )
