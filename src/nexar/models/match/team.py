"""Team and objective-related models."""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .participant import Participant


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

    horde: Objective
    """TODO"""

    inhibitor: Objective
    """Inhibitor objective stats."""

    rift_herald: Objective
    """Rift Herald objective stats."""

    tower: Objective
    """Tower objective stats."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Objectives":
        """Create Objectives from API response."""
        return cls(
            baron=Objective.from_api_response(data["baron"]),
            champion=Objective.from_api_response(data["champion"]),
            dragon=Objective.from_api_response(data["dragon"]),
            horde=Objective.from_api_response(data["horde"]),
            inhibitor=Objective.from_api_response(data["inhibitor"]),
            rift_herald=Objective.from_api_response(data["riftHerald"]),
            tower=Objective.from_api_response(data["tower"]),
        )


@dataclass(frozen=True)
class Team:
    """Represents a team in a match."""

    team_id: int
    """Team identifier (100 for blue, 200 for red)."""

    win: bool
    """Whether this team won the match."""

    bans: list[Ban]
    """List of champion bans for this team."""

    objectives: Objectives
    """Objectives taken by this team."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Team":
        """Create Team from API response."""
        return cls(
            team_id=data["teamId"],
            win=data["win"],
            bans=[Ban.from_api_response(ban) for ban in data["bans"]],
            objectives=Objectives.from_api_response(data["objectives"]),
        )


@dataclass(frozen=True)
class TeamInfo:
    """Enhanced team information with participants and aggregated stats."""

    team_id: int
    """Team identifier (100 for blue, 200 for red)."""

    win: bool
    """Whether this team won the match."""

    bans: list[Ban]
    """List of champion bans for this team."""

    objectives: Objectives
    """Objectives taken by this team."""

    participants: list["Participant"]
    """List of participants on this team."""

    @property
    def total_damage(self) -> int:
        """Total damage dealt to champions by all team members."""
        return sum(p.total_damage_dealt_to_champions for p in self.participants)

    @property
    def total_damage_taken(self) -> int:
        """Total damage taken by all team members."""
        return sum(p.total_damage_taken for p in self.participants)

    @property
    def total_gold_earned(self) -> int:
        """Total gold earned by all team members."""
        return sum(p.gold_earned for p in self.participants)

    @property
    def total_kills(self) -> int:
        """Total kills by all team members."""
        return sum(p.kills for p in self.participants)

    @property
    def total_deaths(self) -> int:
        """Total deaths by all team members."""
        return sum(p.deaths for p in self.participants)

    @property
    def total_assists(self) -> int:
        """Total assists by all team members."""
        return sum(p.assists for p in self.participants)

    @property
    def total_vision_score(self) -> int:
        """Total vision score by all team members."""
        return sum(p.vision_score for p in self.participants)


@dataclass(frozen=True)
class TeamsInfo:
    """Container for blue and red team information."""

    blue: TeamInfo
    """Information for the blue side team (team_id=100)."""

    red: TeamInfo
    """Information for the red side team (team_id=200)."""

    def __iter__(self) -> Iterator[TeamInfo]:
        """Allow iteration over teams."""
        yield self.blue
        yield self.red
