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
            perk=data.get("perk", 0),
            var1=data.get("var1", 0),
            var2=data.get("var2", 0),
            var3=data.get("var3", 0),
        )


@dataclass(frozen=True)
class PerkStyle:
    """Represents a perk style."""

    description: str
    selections: tuple["PerkStyleSelection", ...]
    """Selections for this style. A tuple so the frozen dataclass stays hashable."""
    style: int

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "PerkStyle":
        """Create PerkStyle from API response."""
        return cls(
            description=data.get("description", ""),
            selections=tuple(
                PerkStyleSelection.from_api_response(selection) for selection in data.get("selections") or ()
            ),
            style=data.get("style", 0),
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
            defense=data.get("defense", 0),
            flex=data.get("flex", 0),
            offense=data.get("offense", 0),
        )


@dataclass(frozen=True)
class Perks:
    """Represents participant perks."""

    stat_perks: PerkStats
    styles: tuple[PerkStyle, ...]
    """Rune styles. A tuple so the frozen dataclass stays hashable."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Perks":
        """Create Perks from API response."""
        return cls(
            stat_perks=PerkStats.from_api_response(data.get("statPerks") or {}),
            styles=tuple(PerkStyle.from_api_response(style) for style in data.get("styles") or ()),
        )
