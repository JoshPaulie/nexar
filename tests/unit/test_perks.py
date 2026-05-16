"""Unit tests for Perk models."""

from dataclasses import FrozenInstanceError

import pytest

from nexar.models.match.perks import Perks, PerkStats, PerkStyle, PerkStyleSelection


class TestPerkStyleSelection:
    def test_from_api_response(self) -> None:
        data = {"perk": 5001, "var1": 1, "var2": 2, "var3": 3}
        selection = PerkStyleSelection.from_api_response(data)
        assert selection.perk == 5001
        assert selection.var1 == 1
        assert selection.var2 == 2
        assert selection.var3 == 3

    def test_frozen(self) -> None:
        selection = PerkStyleSelection(perk=5001, var1=0, var2=0, var3=0)
        with pytest.raises(FrozenInstanceError):
            selection.perk = 999  # type: ignore[misc]


class TestPerkStyle:
    def test_from_api_response(self) -> None:
        data = {
            "description": "primaryStyle",
            "selections": [
                {"perk": 8005, "var1": 1, "var2": 2, "var3": 3},
                {"perk": 8008, "var1": 4, "var2": 5, "var3": 6},
            ],
            "style": 8000,
        }
        style = PerkStyle.from_api_response(data)
        assert style.description == "primaryStyle"
        assert style.style == 8000
        assert len(style.selections) == 2
        assert isinstance(style.selections[0], PerkStyleSelection)
        assert style.selections[0].perk == 8005
        assert style.selections[1].perk == 8008

    def test_frozen(self) -> None:
        style = PerkStyle(description="primaryStyle", selections=[], style=8000)
        with pytest.raises(FrozenInstanceError):
            style.style = 999  # type: ignore[misc]


class TestPerkStats:
    def test_from_api_response(self) -> None:
        data = {"defense": 5005, "flex": 5008, "offense": 5002}
        stats = PerkStats.from_api_response(data)
        assert stats.defense == 5005
        assert stats.flex == 5008
        assert stats.offense == 5002

    def test_frozen(self) -> None:
        stats = PerkStats(defense=5005, flex=5008, offense=5002)
        with pytest.raises(FrozenInstanceError):
            stats.defense = 999  # type: ignore[misc]


class TestPerks:
    def test_from_api_response(self) -> None:
        data = {
            "statPerks": {"defense": 5005, "flex": 5008, "offense": 5002},
            "styles": [
                {
                    "description": "primaryStyle",
                    "selections": [{"perk": 8008, "var1": 0, "var2": 0, "var3": 0}],
                    "style": 8000,
                },
                {
                    "description": "subStyle",
                    "selections": [{"perk": 9101, "var1": 0, "var2": 0, "var3": 0}],
                    "style": 8100,
                },
            ],
        }
        perks = Perks.from_api_response(data)
        assert isinstance(perks.stat_perks, PerkStats)
        assert perks.stat_perks.offense == 5002
        assert len(perks.styles) == 2
        assert isinstance(perks.styles[0], PerkStyle)
        assert perks.styles[0].style == 8000
        assert perks.styles[1].style == 8100

    def test_frozen(self) -> None:
        perks = Perks(
            stat_perks=PerkStats(defense=5005, flex=5008, offense=5002),
            styles=[],
        )
        with pytest.raises(FrozenInstanceError):
            perks.styles = []  # type: ignore[misc]
