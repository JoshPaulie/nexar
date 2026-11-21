"""Riot account and summoner identity lookups for NexarClient."""

from urllib.parse import quote

from .core import NexarCore
from .enums import Region
from .models import RiotAccount, Summoner


class IdentityMixin(NexarCore):
    """Riot account and summoner identity lookups."""

    # Account API
    async def get_riot_account(
        self,
        game_name: str,
        tag_line: str,
        region: Region | None = None,
    ) -> RiotAccount:
        """Get a Riot account by game name and tag line."""
        game_name = game_name.strip()
        tag_line = tag_line.strip()
        resolved_region = self._resolve_region(region)
        endpoint = f"/riot/account/v1/accounts/by-riot-id/{quote(game_name)}/{quote(tag_line)}"
        data = await self._make_api_call(endpoint, resolved_region.value, resolved_region.account_region)
        return RiotAccount.from_api_response(data)

    async def get_riot_account_by_puuid(
        self,
        puuid: str,
        *,
        region: Region | None = None,
    ) -> RiotAccount:
        """Get a Riot account by PUUID."""
        resolved_region = self._resolve_region(region)
        endpoint = f"/riot/account/v1/accounts/by-puuid/{puuid}"
        data = await self._make_api_call(endpoint, resolved_region.value, resolved_region.account_region)
        return RiotAccount.from_api_response(data)

    # Summoner API
    async def get_summoner_by_puuid(self, puuid: str, region: Region | None = None) -> Summoner:
        """Get a summoner's platform data by PUUID (level, name, profile icon)."""
        resolved_region = self._resolve_region(region)
        endpoint = f"/lol/summoner/v4/summoners/by-puuid/{puuid}"
        data = await self._make_api_call(endpoint, resolved_region.value)
        return Summoner.from_api_response(data)
