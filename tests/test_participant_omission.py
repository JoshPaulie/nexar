"""Tests for Riot's documented response-omission rule on match participants.

Riot's API only includes non-empty values in responses: zeros, false values, empty
strings and nulls are omitted. These tests strip those keys from the recorded match
fixture and assert the models still parse, with sane defaults.
"""

import dataclasses
import json
from pathlib import Path
from typing import Any

import pytest

from nexar.models.match.challenges import Challenges
from nexar.models.match.participant import Participant
from nexar.models.match.perks import Perks, PerkStyle

FIXTURE_PATH = Path(__file__).parent / "mock_responses.json"


def test_defaulted_fields_table_covers_every_participant_field() -> None:
    """The parse table plus the direct reads cover every Participant field exactly once.

    A row dropped from the table (or a direct read converted badly) would leave a
    field silently defaulted to None at parse time instead of its documented value.
    """
    from nexar.models.match.participant import _DEFAULTED_FIELDS

    direct_fields = {
        "puuid",
        "champion_id",
        "champion_name",
        "team_id",
        "participant_id",
        "win",
        "individual_position",
        "team_position",
        "perks",
        "challenges",
        "missions",
    }
    table_fields = [py for _, py, _ in _DEFAULTED_FIELDS]

    assert len(table_fields) == len(set(table_fields)), "duplicate python name in the parse table"
    assert {f.name for f in dataclasses.fields(Participant)} == set(table_fields) | direct_fields


def _load_match() -> dict[str, Any]:
    with FIXTURE_PATH.open() as fh:
        return json.load(fh)["match"]


def _participant_payload(index: int = 0) -> dict[str, Any]:
    """Return a fresh copy of one recorded participant payload."""
    participants: list[dict[str, Any]] = _load_match()["info"]["participants"]
    return json.loads(json.dumps(participants[index]))


def _strip_zero_ints(value: Any) -> Any:  # noqa: ANN401
    """Recursively drop int-valued zero keys, leaving booleans alone."""
    if isinstance(value, dict):
        return {
            key: _strip_zero_ints(item)
            for key, item in value.items()
            if not (isinstance(item, int) and not isinstance(item, bool) and item == 0)
        }
    if isinstance(value, list):
        return [_strip_zero_ints(item) for item in value]
    return value


def _strip_false_booleans(payload: dict[str, Any]) -> dict[str, Any]:
    """Drop every top-level false boolean except ``win`` (a hard read)."""
    return {
        key: value for key, value in payload.items() if not (isinstance(value, bool) and not value and key != "win")
    }


class TestParticipantOmission:
    """Participant parsing must survive omitted zero-valued keys."""

    def test_participant_parses_when_zero_valued_numerics_are_omitted(self) -> None:
        """A payload with every int-valued zero key removed still parses."""
        payload = _strip_zero_ints(_participant_payload(0))

        # Sanity: the fixture really does carry zeros that we then remove.
        assert "allInPings" not in payload
        assert "baronKills" not in payload

        participant = Participant.from_api_response(payload)

        # Omitted numerics default to zero...
        assert participant.all_in_pings == 0
        assert participant.baron_kills == 0
        assert participant.quadra_kills == 0
        assert participant.largest_critical_strike == 0
        assert participant.sight_wards_bought_in_game == 0
        assert participant.objectives_stolen == 0
        assert participant.champion_transform == 0
        # A stripped placement/bounty is genuinely absent, not zero.
        assert participant.placement is None
        assert participant.bounty_level is None
        # ...and genuinely-present values are untouched.
        assert participant.kills == 6
        assert participant.deaths == 7
        assert participant.assists == 10
        assert participant.wards_killed == 2
        assert participant.total_time_spent_dead == 189
        assert participant.champion_name == "Cassiopeia"
        assert participant.champion_id == 69
        assert participant.participant_id == 1

    def test_participant_parses_when_all_false_booleans_are_omitted(self) -> None:
        """A payload with every false boolean stripped still parses; each defaults to False.

        ``win`` is deliberately kept: it stays a hard read (a participant is only
        meaningful with a result), so its omission is not covered here.
        """
        payload = _strip_false_booleans(_participant_payload(0))

        # Sanity: the fixture really does carry false booleans that we then remove.
        assert "firstBloodKill" not in payload
        assert "gameEndedInEarlySurrender" not in payload
        assert "teamEarlySurrendered" not in payload

        participant = Participant.from_api_response(payload)

        # The kept booleans parse with their recorded values...
        assert participant.win is False
        assert participant.eligible_for_progression is True
        # ...and every stripped one defaults to False.
        assert participant.first_blood_kill is False
        assert participant.first_blood_assist is False
        assert participant.first_tower_kill is False
        assert participant.first_tower_assist is False
        assert participant.game_ended_in_early_surrender is False
        assert participant.game_ended_in_surrender is False
        assert participant.team_early_surrendered is False

    def test_participant_parses_without_summoner_name(self) -> None:
        """A missing summonerName parses to None; present, it passes through; the property always warns."""
        missing = _participant_payload(0)
        missing.pop("summonerName")
        participant = Participant.from_api_response(missing)

        assert participant._summoner_name is None
        with pytest.warns(DeprecationWarning, match="summoner_name is deprecated"):
            assert participant.summoner_name is None

        recorded = Participant.from_api_response(_participant_payload(0))
        with pytest.warns(DeprecationWarning, match="summoner_name is deprecated"):
            assert recorded.summoner_name == ""

    def test_participant_parses_without_placement(self) -> None:
        """A payload missing placement (non-TFT games) parses with None."""
        payload = _participant_payload(0)
        payload.pop("placement")

        participant = Participant.from_api_response(payload)

        assert participant.placement is None

    def test_participant_parses_without_position_strings(self) -> None:
        """A payload missing lane/role/summonerId/positions parses with sentinels."""
        payload = _participant_payload(0)
        for key in ("lane", "role", "summonerId", "individualPosition", "teamPosition"):
            payload.pop(key, None)

        participant = Participant.from_api_response(payload)

        assert participant.lane == ""
        assert participant.role == ""
        assert participant.summoner_id == ""
        assert participant.individual_position.value == "Invalid"
        assert participant.team_position.value == "Invalid"


class TestPerkOmission:
    """Perk parsing must survive omitted zero-valued keys."""

    def test_perks_parse_when_zero_vars_are_omitted(self) -> None:
        """Perk selections with omitted var2/var3 zeros parse as zero."""
        payload = _strip_zero_ints(_participant_payload(0)["perks"])

        # Sanity: the fixture's selections carry zeros that we then remove.
        assert payload["styles"][0]["selections"][0] == {"perk": 8112, "var1": 1654}

        perks = Perks.from_api_response(payload)

        selection = perks.styles[0].selections[0]
        assert selection.perk == 8112
        assert selection.var1 == 1654
        assert selection.var2 == 0
        assert selection.var3 == 0

    def test_perks_parse_without_stat_perks(self) -> None:
        """A perks block with no statPerks key parses to zero stat perks."""
        payload = _participant_payload(0)["perks"]
        del payload["statPerks"]

        perks = Perks.from_api_response(payload)

        assert perks.stat_perks.offense == 0
        assert perks.stat_perks.flex == 0
        assert perks.stat_perks.defense == 0

    def test_perk_style_without_description(self) -> None:
        """A perk style with no description key parses to an empty string."""
        payload = _participant_payload(0)["perks"]["styles"][0]
        del payload["description"]

        style = PerkStyle.from_api_response(payload)

        assert style.description == ""


class TestFrozenCollectionsAreHashable:
    """Frozen dataclasses holding collections must be hashable."""

    def test_perks_are_hashable(self) -> None:
        """Perks (styles/selections) hash because the lists are tuples."""
        perks = Perks.from_api_response(_participant_payload(0)["perks"])

        assert isinstance(perks.styles, tuple)
        assert isinstance(perks.styles[0].selections, tuple)
        assert isinstance(hash(perks), int)

    def test_challenges_legendary_item_used_is_a_tuple(self) -> None:
        """legendary_item_used is a tuple so Challenges stays hashable."""
        challenges = Challenges.from_api_response({"legendaryItemUsed": [6655, 6656]})

        assert challenges.legendary_item_used == (6655, 6656)
        assert isinstance(hash(challenges), int)
