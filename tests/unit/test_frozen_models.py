"""Every frozen public model rejects attribute mutation — one family, one table.

The rows here absorbed the per-model immutability tests scattered across the
suite (test_models, test_perks). FrozenInstanceError subclasses AttributeError,
so one assertion covers every frozen dataclass.
"""

from datetime import UTC, datetime

import pytest

from nexar.models import RiotAccount, Summoner
from nexar.models.match.perks import Perks, PerkStats, PerkStyle, PerkStyleSelection


@pytest.mark.parametrize(
    ("model", "field"),
    [
        (RiotAccount(puuid="p", game_name="g", tag_line="t"), "puuid"),
        (
            Summoner(
                summoner_id=None,
                puuid="p",
                profile_icon_id=1,
                revision_date=datetime.fromtimestamp(0, tz=UTC),
                summoner_level=1,
            ),
            "puuid",
        ),
        (PerkStyleSelection(perk=5001, var1=0, var2=0, var3=0), "perk"),
        (PerkStyle(description="primaryStyle", selections=(), style=8000), "style"),
        (PerkStats(defense=5005, flex=5008, offense=5002), "defense"),
        (Perks(stat_perks=PerkStats(defense=0, flex=0, offense=0), styles=()), "styles"),
    ],
)
def test_frozen_models_reject_mutation(model: object, field: str) -> None:
    with pytest.raises(AttributeError):
        setattr(model, field, object())
