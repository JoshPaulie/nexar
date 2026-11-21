"""Champion rotation models (champion-v3)."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ChampionRotations:
    """The champion rotation for a platform.

    Field names mirror the wire exactly: Riot's DTO spells the two pools ``sr``
    and ``newplayer`` (verified against the live payload, 2026-11-21).
    """

    sr: tuple[int, ...]
    """Champion IDs free to all players on Summoner's Rift this rotation."""

    newplayer: tuple[int, ...]
    """Champion IDs available to players under summoner level 11."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "ChampionRotations":
        """Create ChampionRotations from an API response (Riot omits empty values)."""
        return cls(
            sr=tuple(data.get("sr", ())),
            newplayer=tuple(data.get("newplayer", ())),
        )
