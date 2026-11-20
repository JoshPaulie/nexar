"""Unit tests for Perk models."""

import pytest

from nexar.models.match.perks import Perks, PerkStats, PerkStyle, PerkStyleSelection


@pytest.mark.parametrize(
    ("parser", "payload", "expected"),
    [
        (
            PerkStyleSelection,
            {"perk": 5001, "var1": 1, "var2": 2, "var3": 3},
            PerkStyleSelection(perk=5001, var1=1, var2=2, var3=3),
        ),
        (
            PerkStyle,
            {
                "description": "primaryStyle",
                "selections": [
                    {"perk": 8005, "var1": 1, "var2": 2, "var3": 3},
                    {"perk": 8008, "var1": 4, "var2": 5, "var3": 6},
                ],
                "style": 8000,
            },
            PerkStyle(
                description="primaryStyle",
                selections=(
                    PerkStyleSelection(perk=8005, var1=1, var2=2, var3=3),
                    PerkStyleSelection(perk=8008, var1=4, var2=5, var3=6),
                ),
                style=8000,
            ),
        ),
        (
            PerkStats,
            {"defense": 5005, "flex": 5008, "offense": 5002},
            PerkStats(defense=5005, flex=5008, offense=5002),
        ),
        (
            Perks,
            {
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
            },
            Perks(
                stat_perks=PerkStats(defense=5005, flex=5008, offense=5002),
                styles=(
                    PerkStyle(
                        description="primaryStyle",
                        selections=(PerkStyleSelection(perk=8008, var1=0, var2=0, var3=0),),
                        style=8000,
                    ),
                    PerkStyle(
                        description="subStyle",
                        selections=(PerkStyleSelection(perk=9101, var1=0, var2=0, var3=0),),
                        style=8100,
                    ),
                ),
            ),
        ),
    ],
)
def test_from_api_response(parser, payload, expected) -> None:
    """Each perk parser maps its recorded payload onto the exact model value."""
    assert parser.from_api_response(payload) == expected
