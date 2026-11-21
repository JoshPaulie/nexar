"""Main client for the Nexar SDK.

``NexarClient`` is assembled from topic mixins — identity, league, platform,
challenges, match, plumbing — over the shared seam declared in ``core.py``.
"""

from dataclasses import fields
from types import TracebackType
from typing import TYPE_CHECKING, Self

from .cache import DEFAULT_CACHE_CONFIG, CacheConfig
from .client_challenges import ChallengesMixin
from .client_identity import IdentityMixin
from .client_league import LeagueMixin
from .client_match import MatchMixin
from .client_platform import PlatformMixin
from .client_plumbing import CallStats, PlumbingMixin
from .enums import Region
from .exceptions import BatchError, gather_partitioned
from .models import Player
from .rate_limiter import PERSONAL_LIMITS, RateLimiter

if TYPE_CHECKING:
    import aiohttp
    from aiohttp_client_cache.session import CachedSession

__all__ = [
    "CallStats",
    "NexarClient",
]


class NexarClient(
    IdentityMixin,
    LeagueMixin,
    PlatformMixin,
    ChallengesMixin,
    MatchMixin,
    PlumbingMixin,
):
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
        """Fetch several Players at once.

        Raises ``BatchError`` carrying the successful players when any
        lookup fails.
        """
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
