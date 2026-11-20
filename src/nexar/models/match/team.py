"""Team and objective-related models."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Ban:
    """Represents a champion ban."""

    champion_id: int
    """ID of the banned champion."""

    pick_turn: int
    """The pick/ban turn number when this ban occurred."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Ban":
        """Create Ban from API response."""
        return cls(
            champion_id=data["championId"],
            pick_turn=data["pickTurn"],
        )


@dataclass(frozen=True)
class Objective:
    """Represents an objective (baron, dragon, etc.)."""

    first: bool
    """Whether this objective was taken first by the team."""

    kills: int
    """Number of times this objective was taken by the team."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Objective":
        """Create Objective from API response."""
        return cls(
            first=data["first"],
            kills=data["kills"],
        )


@dataclass(frozen=True)
class Objectives:
    """Represents team objectives."""

    baron: Objective
    """Baron Nashor objective stats."""

    champion: Objective
    """Champion takedown objective stats."""

    dragon: Objective
    """Dragon objective stats."""

    inhibitor: Objective
    """Inhibitor objective stats."""

    rift_herald: Objective
    """Rift Herald objective stats."""

    tower: Objective
    """Tower objective stats."""

    horde: Objective | None = None
    """Voidgrub objective stats (Voidgrubs were added in patch 14.1).

    None for matches played before patch 14.1, where Riot omits the key entirely.
    """

    atakhan: Objective | None = None
    """Atakhan objective stats (Atakhan was added in the 2025 season).

    None for matches played before the 2025 season, where Riot omits the key entirely.
    """

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Objectives":
        """Create Objectives from API response.

        Riot only includes non-empty values, so ``horde`` and ``atakhan`` are optional
        and parsed with ``.get``; either may be None for older matches.
        """
        horde = data.get("horde")
        atakhan = data.get("atakhan")
        return cls(
            baron=Objective.from_api_response(data["baron"]),
            champion=Objective.from_api_response(data["champion"]),
            dragon=Objective.from_api_response(data["dragon"]),
            inhibitor=Objective.from_api_response(data["inhibitor"]),
            rift_herald=Objective.from_api_response(data["riftHerald"]),
            tower=Objective.from_api_response(data["tower"]),
            horde=Objective.from_api_response(horde) if horde else None,
            atakhan=Objective.from_api_response(atakhan) if atakhan else None,
        )


@dataclass(frozen=True)
class Team:
    """Represents a team in a match."""

    team_id: int
    """Team identifier (100 for blue, 200 for red)."""

    win: bool
    """Whether this team won the match."""

    bans: tuple[Ban, ...] | None = None
    """Tuple of champion bans for this team. May be None for some game modes."""

    objectives: Objectives | None = None
    """Objectives taken by this team. May be None for some game modes."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Team":
        """Create Team from API response."""
        return cls(
            team_id=data["teamId"],
            win=data["win"],
            bans=tuple(Ban.from_api_response(ban) for ban in data.get("bans", [])),
            objectives=Objectives.from_api_response(obj_data) if (obj_data := data.get("objectives")) else None,
        )
