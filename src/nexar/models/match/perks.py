"""Perk and rune-related models."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PerkStyleSelection:
    """Represents a perk style selection."""

    perk: int
    var1: int
    var2: int
    var3: int

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "PerkStyleSelection":
        """Create PerkStyleSelection from API response."""
        return cls(
            perk=data["perk"],
            var1=data["var1"],
            var2=data["var2"],
            var3=data["var3"],
        )


@dataclass(frozen=True)
class PerkStyle:
    """Represents a perk style."""

    description: str
    selections: list["PerkStyleSelection"]
    style: int

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "PerkStyle":
        """Create PerkStyle from API response."""
        return cls(
            description=data["description"],
            selections=[
                PerkStyleSelection.from_api_response(selection)
                for selection in data["selections"]
            ],
            style=data["style"],
        )


@dataclass(frozen=True)
class PerkStats:
    """Represents perk stats."""

    defense: int
    flex: int
    offense: int

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "PerkStats":
        """Create PerkStats from API response."""
        return cls(
            defense=data["defense"],
            flex=data["flex"],
            offense=data["offense"],
        )


@dataclass(frozen=True)
class Perks:
    """Represents participant perks."""

    stat_perks: PerkStats
    styles: list[PerkStyle]

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Perks":
        """Create Perks from API response."""
        return cls(
            stat_perks=PerkStats.from_api_response(data["statPerks"]),
            styles=[PerkStyle.from_api_response(style) for style in data["styles"]],
        )
