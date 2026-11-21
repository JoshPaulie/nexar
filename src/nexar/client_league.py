"""Ranked ladder and division-entry lookups for NexarClient."""

from typing import Any, cast

from .core import NexarCore
from .enums import Queue, RankDivision, RankTier, Region
from .models import LeagueEntry, LeagueList

# Ranked ladder queues as Riot's league paths spell them — Queue enum values are
# numeric queue IDs, not the strings these endpoints take. The reference also
# lists RANKED_FLEX_TT, dead since the 2019 Twisted Treeline removal; passing
# it would only buy a 404, so non-ranked and legacy queues raise ValueError.
_LADDER_QUEUES: dict[Queue, str] = {
    Queue.RANKED_SOLO_5x5: "RANKED_SOLO_5x5",
    Queue.RANKED_FLEX_SR: "RANKED_FLEX_SR",
}


# Apex tiers have no divisions, so the division ladder paths do not serve them.
_APEX_TIERS = {RankTier.MASTER, RankTier.GRANDMASTER, RankTier.CHALLENGER}


class LeagueMixin(NexarCore):
    """Ranked ladder and division-entry lookups."""

    # League API
    async def get_league_entries_by_puuid(
        self,
        puuid: str,
        region: Region | None = None,
    ) -> list[LeagueEntry]:
        """Get a player's current ranked entries — one per queue they hold a rank in."""
        resolved_region = self._resolve_region(region)
        endpoint = f"/lol/league/v4/entries/by-puuid/{puuid}"
        data = await self._make_api_call(endpoint, resolved_region.value)
        entries_list = cast("list[dict[str, Any]]", data)
        return [LeagueEntry.from_api_response(entry) for entry in entries_list]

    async def get_challenger_league(
        self,
        queue: Queue,
        region: Region | None = None,
    ) -> LeagueList:
        """Get the challenger ladder for a ranked queue.

        The full ladder arrives in one response — challenger is capped at 300
        players, and there is no page parameter. Entries are pre-sorted by LP.
        """
        resolved_region = self._resolve_region(region)
        endpoint = f"/lol/league/v4/challengerleagues/by-queue/{self._ladder_queue_path(queue)}"
        data = await self._make_api_call(endpoint, resolved_region.value)
        return LeagueList.from_api_response(data)

    async def get_grandmaster_league(
        self,
        queue: Queue,
        region: Region | None = None,
    ) -> LeagueList:
        """Get the grandmaster ladder for a ranked queue.

        The full ladder arrives in one response — grandmaster is capped at 700
        players, and there is no page parameter. Entries are pre-sorted by LP.
        """
        resolved_region = self._resolve_region(region)
        endpoint = f"/lol/league/v4/grandmasterleagues/by-queue/{self._ladder_queue_path(queue)}"
        data = await self._make_api_call(endpoint, resolved_region.value)
        return LeagueList.from_api_response(data)

    async def get_master_league(
        self,
        queue: Queue,
        region: Region | None = None,
    ) -> LeagueList:
        """Get the master ladder for a ranked queue.

        The full ladder arrives in one response: every master-tier player the
        platform serves (exactly 10,000 entries on NA when measured — the entry
        count, not an LP threshold), with no page parameter. Entries are
        pre-sorted by LP.
        """
        resolved_region = self._resolve_region(region)
        endpoint = f"/lol/league/v4/masterleagues/by-queue/{self._ladder_queue_path(queue)}"
        data = await self._make_api_call(endpoint, resolved_region.value)
        return LeagueList.from_api_response(data)

    async def get_league_entries(
        self,
        queue: Queue,
        tier: RankTier,
        division: RankDivision,
        region: Region | None = None,
        *,
        page: int = 1,
    ) -> list[LeagueEntry]:
        """Get one page of a ranked division ladder.

        Each page holds 205 players (measured from the live wire — the current
        reference op block no longer states a page size); iterate ``page`` to
        walk the full division. Apex tiers have no divisions, so ``tier`` must
        be IRON through DIAMOND. The wire does not order a division page by LP
        (measured: Gold I page 1 arrives unsorted) — sort with
        ``LeagueEntry.rank_tuple`` when rank order matters.
        """
        return await self._division_page("/lol/league/v4/entries", queue, tier, division, region, page)

    async def get_league_exp_entries(
        self,
        queue: Queue,
        tier: RankTier,
        division: RankDivision,
        region: Region | None = None,
        *,
        page: int = 1,
    ) -> list[LeagueEntry]:
        """Get one page of a division ladder from the expanded league (league-exp-v4).

        For the LoL ranked queues this serves the same unordered 205-player
        pages in the same order as ``get_league_entries``; individual LP and
        win/loss values drift between the two calls because the ladder keeps
        moving — each page is its own snapshot. The expanded league exists to
        also cover non-LoL queue types.
        """
        return await self._division_page("/lol/league-exp/v4/entries", queue, tier, division, region, page)

    def _ladder_queue_path(self, queue: Queue) -> str:
        """Resolve a Queue to the queue string Riot's league paths take.

        The Queue enum values are numeric IDs, so a raw ``queue.value`` would
        put '420' in a path that needs 'RANKED_SOLO_5x5'.
        """
        if queue not in _LADDER_QUEUES:
            msg = f"queue must be a ranked ladder queue (RANKED_SOLO_5x5 or RANKED_FLEX_SR), got {queue.name}"
            raise ValueError(msg)
        return _LADDER_QUEUES[queue]

    @staticmethod
    def _validate_division_ladder(tier: RankTier, division: RankDivision, page: int) -> None:
        """Reject path values the division ladders do not serve, before any wire call."""
        if tier in _APEX_TIERS:
            msg = f"tier must be a division tier (IRON through DIAMOND), got {tier.value}"
            raise ValueError(msg)
        if division is RankDivision.EMPTY:
            msg = "division must be a real division (I, II, III or IV)"
            raise ValueError(msg)
        if page < 1:
            msg = f"page must be 1 or greater, got {page}"
            raise ValueError(msg)

    async def _division_page(
        self,
        entries_root: str,
        queue: Queue,
        tier: RankTier,
        division: RankDivision,
        region: Region | None,
        page: int,
    ) -> list[LeagueEntry]:
        """Fetch and parse one division-ladder page under either league root.

        The shared tail of ``get_league_entries`` and ``get_league_exp_entries``
        — the two routes differ only in the root path. Page 1 sends no query
        parameter, as both public routes always have.
        """
        self._validate_division_ladder(tier, division, page)
        resolved_region = self._resolve_region(region)
        params = {"page": page} if page != 1 else None
        endpoint = f"{entries_root}/{self._ladder_queue_path(queue)}/{tier.value}/{division.value}"
        data = await self._make_api_call(endpoint, resolved_region.value, params=params)
        entries_list = cast("list[dict[str, Any]]", data)
        return [LeagueEntry.from_api_response(entry) for entry in entries_list]
