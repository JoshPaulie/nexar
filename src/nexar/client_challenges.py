"""lol-challenges-v1 lookups for NexarClient."""

from typing import Any, cast

from .core import NexarCore
from .enums import ChallengeLevel, Region
from .models import ChallengeConfig, ChallengeLeaderboardEntry, PlayerChallengeData

# Challenge leaderboards only serve the apex levels — the other ten legal
# ChallengeLevel values belong to progress rows and percentile maps, and the
# leaderboard path answers 400 for them (measured 2026-11-21 on NA1).
_LEADERBOARD_LEVELS = {
    ChallengeLevel.MASTER,
    ChallengeLevel.GRANDMASTER,
    ChallengeLevel.CHALLENGER,
}


class ChallengesMixin(NexarCore):
    """lol-challenges-v1 lookups."""

    # Challenges API
    # All six ops route per-platform like summoner/mastery: the regional hosts
    # (americas/europe/asia) answer 403 for this family even though account-v1
    # shares its docs page shape (measured 2026-11-21; Riot's spec consts agree).
    async def get_all_challenge_configs(self, region: Region | None = None) -> list[ChallengeConfig]:
        """Get every challenge's configuration.

        The full catalog in one call — 405 challenges on NA at recording. The
        wire sends id, localizedNames, state, leaderboard, and thresholds on
        every entry plus endTimestamp on exactly one (challenge 600012); the
        DTO table's tracking and startTimestamp never appear.
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

        Keys are strings, as JSON object keys always are, so look them up
        with ``str(config.id)``. The wire is a flat challengeId -> level
        -> percentile map; the reference DTO's extra ``Map[Integer, ...>``
        layer does not exist.
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
