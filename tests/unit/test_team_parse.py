"""Team, Ban, and Objective parse tests.

TeamInfo/TeamsInfo were deleted with their dead API: nothing in src could
construct them (audit R2), so their fixture-heavy tests went with them. What
remains pins the parsing contract of the models match parsing actually uses.
"""

import pytest

from nexar.models.match.team import Ban, Objective, Objectives, Team


class TestTeamParse:
    def test_from_api_response(self) -> None:
        """A recorded team payload parses to its exact Team: bans' contents, a loss, omitted objectives."""
        team = Team.from_api_response(
            {
                "teamId": 100,
                "win": False,
                "bans": [
                    {"championId": 238, "pickTurn": 1},
                    {"championId": 7, "pickTurn": 2},
                ],
                "objectives": {
                    "baron": {"first": True, "kills": 1},
                    "champion": {"first": True, "kills": 10},
                    "dragon": {"first": False, "kills": 2},
                    "inhibitor": {"first": True, "kills": 1},
                    "riftHerald": {"first": True, "kills": 1},
                    "tower": {"first": False, "kills": 5},
                },
            },
        )

        assert team.team_id == 100
        assert team.win is False
        assert team.bans == (Ban(champion_id=238, pick_turn=1), Ban(champion_id=7, pick_turn=2))
        assert team.objectives is not None
        assert team.objectives.baron == Objective(first=True, kills=1)
        assert team.objectives.horde is None
        assert team.objectives.atakhan is None

    def test_ban_from_api_response(self) -> None:
        ban = Ban.from_api_response({"championId": 238, "pickTurn": 1})
        assert ban.champion_id == 238
        assert ban.pick_turn == 1

    def test_objective_from_api_response(self) -> None:
        obj = Objective.from_api_response({"first": True, "kills": 3})
        assert obj.first is True
        assert obj.kills == 3

    def test_team_is_hashable(self) -> None:
        """The frozen team (tuple bans, nested objectives) hashes without raising."""
        team = Team.from_api_response(
            {
                "teamId": 100,
                "win": True,
                "bans": [{"championId": 1, "pickTurn": 1}],
                "objectives": {
                    "baron": {"first": True, "kills": 1},
                    "champion": {"first": True, "kills": 10},
                    "dragon": {"first": False, "kills": 2},
                    "inhibitor": {"first": False, "kills": 0},
                    "riftHerald": {"first": True, "kills": 1},
                    "tower": {"first": True, "kills": 5},
                },
            },
        )

        assert team.bans is not None
        assert hash(team) == hash(team)


class TestObjectivesOptionalFields:
    """Objectives keys that Riot omits for some game versions.

    Riot's API responses include only non-empty values, so pre-14.1 matches have no
    ``horde`` (Voidgrubs) and matches before the 2025 season have no ``atakhan``.
    """

    @staticmethod
    def payload(**overrides: object) -> dict[str, object]:
        data: dict[str, object] = {
            "baron": {"first": True, "kills": 1},
            "champion": {"first": True, "kills": 10},
            "dragon": {"first": False, "kills": 2},
            "inhibitor": {"first": False, "kills": 0},
            "riftHerald": {"first": True, "kills": 1},
            "tower": {"first": True, "kills": 5},
        }
        data.update(overrides)
        return data

    @pytest.mark.parametrize("omitted", ["horde", "atakhan"])
    def test_payload_without_optional_objective_parses_to_none(self, omitted: str) -> None:
        """A payload missing horde (pre-14.1) or atakhan (pre-2025) parses it to None."""
        objectives = Objectives.from_api_response(self.payload())

        assert getattr(objectives, omitted) is None
        assert objectives.baron.kills == 1

    def test_payload_with_horde_and_atakhan_parses_both(self) -> None:
        """A 2025+ payload contains horde (Voidgrubs) and atakhan."""
        objectives = Objectives.from_api_response(
            self.payload(
                horde={"first": False, "kills": 3},
                atakhan={"first": True, "kills": 1},
            ),
        )

        assert objectives.horde is not None
        assert objectives.horde.kills == 3
        assert objectives.atakhan is not None
        assert objectives.atakhan.first is True
        assert objectives.atakhan.kills == 1
