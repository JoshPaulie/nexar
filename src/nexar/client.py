"""Main client for the Nexar SDK."""

import asyncio
import json
import logging
import math
import os
import sqlite3
from dataclasses import dataclass, fields
from datetime import UTC, datetime
from types import TracebackType
from typing import Any, Self, cast
from urllib.parse import quote

import aiohttp
from aiohttp_client_cache.session import CachedSession

from .cache import DEFAULT_CACHE_CONFIG, CacheConfig, create_cache_backend
from .enums import ChallengeLevel, MatchType, Queue, RankDivision, RankTier, Region
from .exceptions import (
    BatchError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    RiotAPIError,
    UnauthorizedError,
    gather_partitioned,
)
from .models import (
    ChallengeConfig,
    ChallengeLeaderboardEntry,
    ChampionMastery,
    ChampionRotations,
    LeagueEntry,
    LeagueList,
    Match,
    PlatformStatus,
    Player,
    PlayerChallengeData,
    RiotAccount,
    Summoner,
    Timeline,
)
from .rate_limiter import PERSONAL_LIMITS, RateLimiter

logger = logging.getLogger("nexar")

__all__ = [
    "CallStats",
    "NexarClient",
]

HTTP_OK = 200
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_TOO_MANY_REQUESTS = 429

MAX_MATCH_ID_COUNT = 100
DEFAULT_MATCH_ID_COUNT = 20
# Fallback 429 block duration when Riot omits or garbles Retry-After.
DEFAULT_RETRY_AFTER_SECONDS = 5.0

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

# Challenge leaderboards only serve the apex levels — the other ten legal
# ChallengeLevel values belong to progress rows and percentile maps, and the
# leaderboard path answers 400 for them (measured 2026-11-21 on NA1).
_LEADERBOARD_LEVELS = {
    ChallengeLevel.MASTER,
    ChallengeLevel.GRANDMASTER,
    ChallengeLevel.CHALLENGER,
}


@dataclass(frozen=True)
class CallStats:
    """Statistics about API calls made by the client."""

    cache_hits: int
    """Number of responses served from cache."""

    fresh_calls: int
    """Number of responses fetched from the Riot API."""

    retries: int
    """Number of retry attempts (429 rate limits or transient network errors)."""

    errors: int
    """Number of non-retryable errors."""

    @property
    def total_calls(self) -> int:
        """Total number of API call attempts."""
        return self.cache_hits + self.fresh_calls + self.retries + self.errors


class NexarClient:
    """Client for interacting with the Riot Games API."""

    def __init__(
        self,
        riot_api_key: str,
        default_region: Region | None = None,
        cache_config: CacheConfig | None = None,
        app_rate_limits: tuple[tuple[int, int], ...] = PERSONAL_LIMITS,
    ) -> None:
        """
        Initialize the Nexar client.

        Args:
            riot_api_key: Your Riot Games API key.
            default_region: Default region for API calls.
            cache_config: Cache configuration (uses DEFAULT_CACHE_CONFIG if None).
            app_rate_limits: Application-level rate limits as (count, window_seconds) tuples.
                Defaults to PERSONAL_LIMITS (20 req/1s + 100 req/120s).
                For production keys use PRODUCTION_LIMITS: ((500, 10), (30000, 600)).

        """
        self.riot_api_key = riot_api_key
        self.default_region = default_region
        self.cache_config = cache_config or DEFAULT_CACHE_CONFIG
        self.rate_limiter = RateLimiter(app_rate_limits)

        self._api_call_count = 0
        # Mutable tally over the CallStats field names; CallStats(**self._call_stats)
        # and this dict share one key source, the dataclass definition.
        self._call_stats: dict[str, int] = dict.fromkeys((f.name for f in fields(CallStats)), 0)
        self._session: CachedSession | aiohttp.ClientSession | None = None

    async def __aenter__(self) -> Self:
        await self._ensure_session()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    # --------------------------------------------------------------------------
    # Public API Methods
    # --------------------------------------------------------------------------

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
        resolved_region = self._resolve_region(region)
        endpoint = f"/lol/summoner/v4/summoners/by-puuid/{puuid}"
        data = await self._make_api_call(endpoint, resolved_region.value)
        return Summoner.from_api_response(data)

    # League API
    async def get_league_entries_by_puuid(
        self,
        puuid: str,
        region: Region | None = None,
    ) -> list[LeagueEntry]:
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
        self._validate_division_ladder(tier, division, page)
        resolved_region = self._resolve_region(region)
        params = {"page": page} if page != 1 else None
        endpoint = f"/lol/league/v4/entries/{self._ladder_queue_path(queue)}/{tier.value}/{division.value}"
        data = await self._make_api_call(endpoint, resolved_region.value, params=params)
        entries_list = cast("list[dict[str, Any]]", data)
        return [LeagueEntry.from_api_response(entry) for entry in entries_list]

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
        self._validate_division_ladder(tier, division, page)
        resolved_region = self._resolve_region(region)
        params = {"page": page} if page != 1 else None
        endpoint = f"/lol/league-exp/v4/entries/{self._ladder_queue_path(queue)}/{tier.value}/{division.value}"
        data = await self._make_api_call(endpoint, resolved_region.value, params=params)
        entries_list = cast("list[dict[str, Any]]", data)
        return [LeagueEntry.from_api_response(entry) for entry in entries_list]

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

    # Challenges API
    # All six ops route per-platform like summoner/mastery: the regional hosts
    # (americas/europe/asia) answer 403 for this family even though account-v1
    # shares its docs page shape (measured 2026-11-21; Riot's spec consts agree).
    async def get_all_challenge_configs(self, region: Region | None = None) -> list[ChallengeConfig]:
        """Get every challenge's configuration.

        The full catalog in one call — 405 challenges on NA at recording. The
        wire sends only id, localizedNames, state, leaderboard, and
        thresholds; the DTO table's tracking/timestamp fields never appear.
        """
        resolved_region = self._resolve_region(region)
        endpoint = "/lol/challenges/v1/challenges/config"
        data = await self._make_api_call(endpoint, resolved_region.value)
        configs_list = cast("list[dict[str, Any]]", data)
        return [ChallengeConfig.from_api_response(entry) for entry in configs_list]

    async def get_challenge_config(self, challenge_id: int, region: Region | None = None) -> ChallengeConfig:
        """Get one challenge's configuration by id."""
        resolved_region = self._resolve_region(region)
        endpoint = f"/lol/challenges/v1/challenges/{challenge_id}/config"
        data = await self._make_api_call(endpoint, resolved_region.value)
        return ChallengeConfig.from_api_response(data)

    async def get_all_challenge_percentiles(self, region: Region | None = None) -> dict[str, dict[str, float]]:
        """Get percentile maps for every challenge, keyed by challenge id.

        The wire is a flat challengeId -> level -> percentile map; the
        reference DTO's extra ``Map[Integer, ...>`` layer does not exist.
        """
        resolved_region = self._resolve_region(region)
        endpoint = "/lol/challenges/v1/challenges/percentiles"
        return await self._make_api_call(endpoint, resolved_region.value)

    async def get_challenge_percentiles(self, challenge_id: int, region: Region | None = None) -> dict[str, float]:
        """Get one challenge's level-to-percentile map.

        Levels that exist as thresholds appear as keys, plus NONE — the share
        of players with no progress, which measured exactly 1.0 on the
        CRYSTAL challenge.
        """
        resolved_region = self._resolve_region(region)
        endpoint = f"/lol/challenges/v1/challenges/{challenge_id}/percentiles"
        return await self._make_api_call(endpoint, resolved_region.value)

    async def get_challenge_leaderboard(
        self,
        challenge_id: int,
        level: ChallengeLevel | str,
        region: Region | None = None,
        *,
        limit: int | None = None,
    ) -> list[ChallengeLeaderboardEntry]:
        """Get a challenge's leaderboard for one level.

        Only the apex levels serve — MASTER, GRANDMASTER and CHALLENGER. The
        other ten legal ``ChallengeLevel`` values belong to progress rows,
        and the leaderboard path answers 400 for them (measured 2026-11-21 on
        NA1), so an enum input for a non-apex level raises ``ValueError``
        before any wire call; a raw string passes through unvalidated. The
        optional ``limit`` truncates the board from the front.

        Entries arrive sorted by position (measured), and positions are
        global across the challenge's tiers — the MASTER board for the
        CRYSTAL challenge starts at 58, with 1-57 sitting in the tiers above.
        """
        if limit is not None and limit < 1:
            msg = f"limit must be positive, got {limit}"
            raise ValueError(msg)
        level_path = self._leaderboard_level_path(level)
        resolved_region = self._resolve_region(region)
        params = {"limit": limit} if limit is not None else None
        endpoint = f"/lol/challenges/v1/challenges/{challenge_id}/leaderboards/by-level/{level_path}"
        data = await self._make_api_call(endpoint, resolved_region.value, params=params)
        entries_list = cast("list[dict[str, Any]]", data)
        return [ChallengeLeaderboardEntry.from_api_response(entry) for entry in entries_list]

    async def get_player_challenge_data(self, puuid: str, region: Region | None = None) -> PlayerChallengeData:
        """Get a player's challenge system data.

        Per-challenge progress, point totals per category and overall, and
        their challenge customization — the one player-centric op of the
        family, also reachable as ``Player.get_challenge_data()``.
        """
        resolved_region = self._resolve_region(region)
        endpoint = f"/lol/challenges/v1/player-data/{puuid}"
        data = await self._make_api_call(endpoint, resolved_region.value)
        return PlayerChallengeData.from_api_response(data)

    # Match API
    async def get_match(self, match_id: str, region: Region | None = None) -> Match:
        resolved_region = self._resolve_region(region)
        endpoint = f"/lol/match/v5/matches/{match_id}"
        data = await self._make_api_call(endpoint, resolved_region.value, resolved_region.v5_region)
        return Match.from_api_response(data)

    async def get_match_timeline(self, match_id: str, region: Region | None = None) -> Timeline:
        """Get a match's timeline: per-minute participant frames plus the event stream."""
        resolved_region = self._resolve_region(region)
        endpoint = f"/lol/match/v5/matches/{match_id}/timeline"
        data = await self._make_api_call(endpoint, resolved_region.value, resolved_region.v5_region)
        return Timeline.from_api_response(data)

    async def get_match_ids_by_puuid(
        self,
        puuid: str,
        *,
        start_time: int | datetime | None = None,
        end_time: int | datetime | None = None,
        queue: Queue | int | None = None,
        match_type: MatchType | str | None = None,
        start: int = 0,
        count: int = DEFAULT_MATCH_ID_COUNT,
        region: Region | None = None,
    ) -> list[str]:
        if start < 0:
            msg = f"start must be non-negative, got {start}"
            raise ValueError(msg)
        if not 0 <= count <= MAX_MATCH_ID_COUNT:
            msg = f"count must be between 0 and {MAX_MATCH_ID_COUNT}"
            raise ValueError(msg)

        resolved_region = self._resolve_region(region)
        params = self._build_match_ids_params(start_time, end_time, queue, match_type, start, count)
        endpoint = f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
        data = await self._make_api_call(endpoint, resolved_region.value, resolved_region.v5_region, params=params)
        return cast("list[str]", data)

    # --------------------------------------------------------------------------
    # High-Level Convenience Methods
    # --------------------------------------------------------------------------

    async def get_player(
        self,
        *,
        game_name: str | None = None,
        tag_line: str | None = None,
        puuid: str | None = None,
        riot_id: str | None = None,
        region: Region | None = None,
    ) -> "Player":
        """
        Get a Player by game name + tag line, PUUID, or Riot ID string.

        The identification precedence lives on ``Player.create``, which this
        forwards to: ``game_name`` + ``tag_line``, then ``puuid``, then
        ``riot_id`` — the first complete pattern wins. The region is resolved
        against the client default here, so the returned ``Player.region`` is
        always concrete.

        Args:
            game_name: Player's game name (without #). Must be paired with tag_line.
            tag_line: Player's tag line (without #). Must be paired with game_name.
            puuid: Player's PUUID for direct lookup.
            riot_id: Riot ID in "gameName#tagLine" format (e.g. "bexli#bex").
            region: The player's region (defaults to client default).

        Returns:
            Player instance with riot account data pre-fetched.

        Raises:
            ValueError: If no identification is provided.

        """
        resolved_region = self._resolve_region(region)
        return await Player.create(
            client=self,
            game_name=game_name,
            tag_line=tag_line,
            puuid=puuid,
            riot_id=riot_id,
            region=resolved_region,
        )

    async def get_players(
        self,
        riot_ids: list[str],
        region: Region | None = None,
    ) -> list["Player"]:
        resolved_region = self._resolve_region(region)

        async def create_player(riot_id: str) -> Player:
            return await Player.by_riot_id(
                client=self,
                riot_id=riot_id,
                region=resolved_region,
            )

        players, errors = await gather_partitioned(riot_ids, create_player)
        if errors:
            raise BatchError(errors, successful_results=players)
        return players

    # --------------------------------------------------------------------------
    # Public Utility Methods
    # --------------------------------------------------------------------------

    async def clear_cache(self) -> None:
        if isinstance(self._session, CachedSession) and self._session.cache:
            await self._session.cache.clear()
            logger.info("Cache cleared")

    async def get_cache_info(self) -> dict[str, Any]:
        """Report the cache configuration and the number of stored rows.

        ``cached_responses`` is a best-effort count: a storage that cannot be
        counted (e.g. a locked sqlite file) reports 0 rather than raising.
        """
        info: dict[str, Any] = {
            "enabled": self.cache_config.enabled,
            "backend": self.cache_config.backend,
            "cache_name": self.cache_config.cache_name,
            "default_expire_after": self.cache_config.expire_after,
            "cached_responses": 0,
        }

        session = self._session
        if isinstance(session, CachedSession) and session.cache:
            try:
                # Row count via the storage's size(): every BaseCache implements
                # it, while CacheBackend itself defines no __len__ in this
                # aiohttp-client-cache version.
                info["cached_responses"] = await session.cache.responses.size()
            except (OSError, sqlite3.Error) as exc:
                logger.debug("Cache row count failed: %s", exc)

        return info

    def get_api_call_stats(self) -> CallStats:
        return CallStats(**self._call_stats)

    def print_api_call_summary(self) -> None:
        stats = self.get_api_call_stats()
        if stats.total_calls > 0:
            cache_hit_rate = (stats.cache_hits / stats.total_calls) * 100
            logger.info(
                "API Stats: %d calls total, %d fresh, %d cached (%.1f%% cache hit rate), %d retries, %d errors",
                stats.total_calls,
                stats.fresh_calls,
                stats.cache_hits,
                cache_hit_rate,
                stats.retries,
                stats.errors,
            )
        else:
            logger.info("No API calls made yet.")

    # --------------------------------------------------------------------------
    # Internal Methods
    # --------------------------------------------------------------------------

    async def _ensure_session(self) -> CachedSession | aiohttp.ClientSession:
        if self._session and not self._session.closed:
            return self._session

        timeout = aiohttp.ClientTimeout(total=self.cache_config.timeout)

        if self.cache_config.enabled:
            self._session = CachedSession(
                cache=create_cache_backend(self.cache_config),
                timeout=timeout,
            )
        else:
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def _try_cache_response(
        self,
        url: str,
        headers: dict[str, str],
        params: dict[str, Any] | None,
        endpoint: str,
    ) -> dict[str, Any] | None:
        """Try to return a cached response. Returns data on hit, None on miss.

        Load-bearing, not redundant with CachedSession's own interception: this
        read happens before ``rate_limiter.acquire``, so cache hits skip the
        limiter instead of burning a rate-limit slot. The library's interception
        (which cannot skip the limiter) stays unreachable for 200-only rows
        because this path returns them first.
        """
        if not isinstance(self._session, CachedSession) or not self._session.cache:
            return None
        cache_key = self._session.cache.create_key("GET", url, params=params, headers=headers)
        cached_response = await self._session.cache.get_response(cache_key)
        if cached_response and cached_response.ok:
            response_data = await cached_response.json()
            if response_data is None:
                # An empty body is unreadable: drop the row, or the session's own
                # interception serves it again on the wire call that follows.
                await self._session.cache.delete(cache_key)
                return None
            self._call_stats["cache_hits"] += 1
            logger.info("  Success (Status: %d, from cache)", cached_response.status)
            self._debug_print_response(
                endpoint=endpoint,
                url=url,
                status=cached_response.status,
                from_cache=True,
                response_data=response_data,
                params=params,
            )
            return response_data
        return None

    async def _record_fresh_response(
        self,
        response: aiohttp.ClientResponse,
        platform_region: str,
        url: str,
        endpoint: str,
        params: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Orient the limiter, record stats, and return response data.

        ``from_cache`` is read to keep limiter orientation off replayed rows,
        even though only fresh wire responses reach this method: the manual
        cache read above preempts the library's own cache interception.
        """
        if not getattr(response, "from_cache", False):
            counts = self._parse_rate_limit_counts(response.headers.get("X-App-Rate-Limit-Count"))
            if counts:
                # Orient from the server's own usage ledger (no-op after the
                # first seed per region) so a restarted client doesn't
                # re-burst into a partially spent window.
                self.rate_limiter.seed_from_counts(platform_region, counts)
        await self._handle_response_errors(response)
        response_data: dict[str, Any] = await response.json()
        self._call_stats["fresh_calls"] += 1
        logger.info("  Success (Status: %d, fresh)", response.status)
        self._debug_print_response(
            endpoint=endpoint,
            url=url,
            status=response.status,
            from_cache=False,
            response_data=response_data,
            params=params,
        )
        return response_data

    async def _make_api_call(
        self,
        endpoint: str,
        platform_region: str,
        routing_region: str | None = None,
        params: dict[str, Any] | None = None,
        max_retries: int = 5,
    ) -> dict[str, Any]:
        if routing_region is None:
            routing_region = platform_region

        endpoint = "/" + endpoint.lstrip("/")
        url = f"https://{routing_region}.api.riotgames.com{endpoint}"
        headers = {"X-Riot-Token": self.riot_api_key}

        session = await self._ensure_session()

        for _attempt in range(max_retries):
            self._api_call_count += 1
            logger.info("API Call #%d: %s (region: %s)", self._api_call_count, endpoint, platform_region)

            try:
                cached_data = await self._try_cache_response(url, headers, params, endpoint)
                if cached_data is not None:
                    return cached_data

                await self.rate_limiter.acquire(platform_region)

                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == HTTP_TOO_MANY_REQUESTS:
                        retry_after = self._parse_retry_after(response.headers.get("Retry-After"))
                        self._call_stats["retries"] += 1
                        logger.warning(
                            "429 on attempt %d/%d for %s (region: %s). Blocking region for %.1fs",
                            _attempt + 1,
                            max_retries,
                            endpoint,
                            platform_region,
                            retry_after,
                        )
                        self.rate_limiter.block(platform_region, retry_after)
                        continue

                    return await self._record_fresh_response(
                        response,
                        platform_region,
                        url,
                        endpoint,
                        params,
                    )

            except (TimeoutError, aiohttp.ClientConnectionError) as e:
                if _attempt < max_retries - 1:
                    self._call_stats["retries"] += 1
                    backoff = 2**_attempt
                    logger.warning(
                        "Request failed (attempt %d/%d): %s. Retrying in %ds...",
                        _attempt + 1,
                        max_retries,
                        e,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    continue
                raise RiotAPIError(0, f"Request failed after {max_retries} attempts: {e}") from e
            except aiohttp.ClientError as e:
                self._call_stats["errors"] += 1
                logger.exception("Request failed")
                raise RiotAPIError(0, f"Request failed: {e}") from e
            except RiotAPIError as e:
                # 4xx responses are routine control flow: log without a traceback.
                logger.warning("API error: %s", e)
                raise

        msg = f"Max attempts ({max_retries}) exceeded for rate-limited requests."
        raise RateLimitError(HTTP_TOO_MANY_REQUESTS, msg)

    async def _handle_response_errors(self, response: aiohttp.ClientResponse) -> None:
        if response.ok:
            return

        try:
            error_data = await response.json()
            message = error_data.get("status", {}).get("message", "Unknown error")
        except (ValueError, aiohttp.ContentTypeError):
            message = await response.text() or f"HTTP {response.status}"

        error_map = {
            HTTP_UNAUTHORIZED: UnauthorizedError,
            HTTP_FORBIDDEN: ForbiddenError,
            HTTP_NOT_FOUND: NotFoundError,
        }
        error_class = error_map.get(response.status, RiotAPIError)
        self._call_stats["errors"] += 1
        raise error_class(response.status, message)

    def _build_match_ids_params(
        self,
        start_time: int | datetime | None,
        end_time: int | datetime | None,
        queue: Queue | int | None,
        match_type: MatchType | str | None,
        start: int,
        count: int,
    ) -> dict[str, int | str]:
        params: dict[str, int | str] = {}
        if start_time is not None:
            params["startTime"] = self._to_epoch(start_time)
        if end_time is not None:
            params["endTime"] = self._to_epoch(end_time)
        if queue is not None:
            params["queue"] = queue.value if isinstance(queue, Queue) else queue
        if match_type is not None:
            params["type"] = match_type.value if isinstance(match_type, MatchType) else match_type
        if start != 0:
            params["start"] = start
        if count != DEFAULT_MATCH_ID_COUNT:
            params["count"] = count
        return params

    def _ladder_queue_path(self, queue: Queue) -> str:
        """Resolve a Queue to the queue string Riot's league paths take.

        The Queue enum values are numeric IDs, so a raw ``queue.value`` would
        put '420' in a path that needs 'RANKED_SOLO_5x5'.
        """
        if queue not in _LADDER_QUEUES:
            msg = f"queue must be a ranked ladder queue (RANKED_SOLO_5x5 or RANKED_FLEX_SR), got {queue.name}"
            raise ValueError(msg)
        return _LADDER_QUEUES[queue]

    def _leaderboard_level_path(self, level: ChallengeLevel | str) -> str:
        """Resolve a leaderboard level to the path string Riot's op takes.

        A ``ChallengeLevel`` input is validated against the apex levels the
        path actually serves, so a non-apex enum value fails before any wire
        call instead of buying a 400. A raw string passes through as-is —
        Riot's own 400 is the backstop, and ``ChallengeLevel`` covers every
        documented value already.
        """
        if isinstance(level, ChallengeLevel):
            if level not in _LEADERBOARD_LEVELS:
                msg = (
                    "level must be MASTER, GRANDMASTER or CHALLENGER for leaderboards "
                    f"(the other ChallengeLevel values get a 400 on this path), got {level.name}"
                )
                raise ValueError(msg)
            return level.value
        return level

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

    def _resolve_region(self, region: Region | None) -> Region:
        resolved_region = region or self.default_region
        if resolved_region is None:
            msg = "A region must be provided either as a default or as an argument."
            raise ValueError(msg)
        return resolved_region

    @staticmethod
    def _to_epoch(value: int | datetime) -> int:
        """
        Convert int or datetime to UTC epoch seconds.

        Naive datetimes are treated as UTC.
        """
        if isinstance(value, int):
            return value
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return int(value.timestamp())

    @staticmethod
    def _parse_retry_after(value: str | None) -> float:
        """Parse a Retry-After header (seconds). Falls back to a conservative default."""
        if value is None:
            return DEFAULT_RETRY_AFTER_SECONDS
        try:
            seconds = float(value)
        except ValueError:
            logger.warning(
                "Invalid Retry-After header %r. Using default of %.0f seconds",
                value,
                DEFAULT_RETRY_AFTER_SECONDS,
            )
            return DEFAULT_RETRY_AFTER_SECONDS
        if not math.isfinite(seconds):
            # float("nan")/float("inf") parse but block(region, nan) would never block.
            logger.warning(
                "Non-finite Retry-After header %r. Using default of %.0f seconds",
                value,
                DEFAULT_RETRY_AFTER_SECONDS,
            )
            return DEFAULT_RETRY_AFTER_SECONDS
        return seconds

    @staticmethod
    def _parse_rate_limit_counts(value: str | None) -> dict[int, int]:
        """Parse X-App-Rate-Limit-Count ("5:1,90:120") into {window: count}."""
        counts: dict[int, int] = {}
        if not value:
            return counts
        for segment in value.split(","):
            try:
                count_str, window_str = segment.split(":")
                counts[int(window_str)] = int(count_str)
            except ValueError:
                logger.debug("Unparsable rate limit count segment %r; skipping orientation", segment)
        return counts

    def _debug_print_response(
        self,
        endpoint: str,
        url: str,
        status: int,
        *,
        from_cache: bool,
        response_data: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> None:
        if not os.getenv("NEXAR_DEBUG_RESPONSES"):
            return

        print(f"\n{'=' * 60}")
        print(f"DEBUG: API Response for {endpoint}")
        print(f"URL: {url}")
        print(f"Status: {status}")
        print(f"From Cache: {from_cache}")
        if params:
            print(f"Params: {params}")
        print("Response Data:")
        print(json.dumps(response_data, indent=2))
        print(f"{'=' * 60}\n")
