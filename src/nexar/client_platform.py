"""Champion mastery, rotations, and platform status for NexarClient."""

from typing import Any, cast

from .core import NexarCore
from .enums import Region
from .models import ChampionMastery, ChampionRotations, PlatformStatus


class PlatformMixin(NexarCore):
    """Champion mastery, rotations, and platform status."""

    # Champion Mastery API
    async def get_champion_masteries(
        self,
        puuid: str,
        region: Region | None = None,
    ) -> list[ChampionMastery]:
        """Get a player's champion masteries, highest points first."""
        resolved_region = self._resolve_region(region)
        endpoint = f"/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}"
        data = await self._make_api_call(endpoint, resolved_region.value)
        entries_list = cast("list[dict[str, Any]]", data)
        return [ChampionMastery.from_api_response(entry) for entry in entries_list]

    async def get_champion_mastery(
        self,
        puuid: str,
        champion_id: int,
        region: Region | None = None,
    ) -> ChampionMastery:
        """Get a player's mastery for a single champion."""
        resolved_region = self._resolve_region(region)
        endpoint = f"/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/by-champion/{champion_id}"
        data = await self._make_api_call(endpoint, resolved_region.value)
        return ChampionMastery.from_api_response(data)

    async def get_top_champion_masteries(
        self,
        puuid: str,
        region: Region | None = None,
        count: int | None = None,
    ) -> list[ChampionMastery]:
        """Get a player's top champion masteries (Riot's default count is 3)."""
        if count is not None and count < 1:
            msg = f"count must be positive, got {count}"
            raise ValueError(msg)
        resolved_region = self._resolve_region(region)
        params = {"count": count} if count is not None else None
        endpoint = f"/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/top"
        data = await self._make_api_call(endpoint, resolved_region.value, params=params)
        entries_list = cast("list[dict[str, Any]]", data)
        return [ChampionMastery.from_api_response(entry) for entry in entries_list]

    async def get_champion_mastery_score(self, puuid: str, region: Region | None = None) -> int:
        """Get a player's total mastery score across all champions."""
        resolved_region = self._resolve_region(region)
        endpoint = f"/lol/champion-mastery/v4/scores/by-puuid/{puuid}"
        data = await self._make_api_call(endpoint, resolved_region.value)
        return cast("int", data)

    # Champion API
    async def get_champion_rotations(self, region: Region | None = None) -> ChampionRotations:
        """Get the platform's champion rotation.

        Covers the free Summoner's Rift pool and the extra pool for players
        under summoner level 11. Not player-centric — no puuid is involved.
        """
        resolved_region = self._resolve_region(region)
        endpoint = "/lol/platform/v3/champion-rotations"
        data = await self._make_api_call(endpoint, resolved_region.value)
        return ChampionRotations.from_api_response(data)

    # Platform Status API
    async def get_platform_status(self, region: Region | None = None) -> PlatformStatus:
        """Get the platform's service status.

        Covers scheduled and in-progress maintenances plus active incidents.
        Not player-centric — no puuid is involved.
        """
        resolved_region = self._resolve_region(region)
        endpoint = "/lol/status/v4/platform-data"
        data = await self._make_api_call(endpoint, resolved_region.value)
        return PlatformStatus.from_api_response(data)
