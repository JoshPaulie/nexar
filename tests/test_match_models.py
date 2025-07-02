"""Tests for match models."""

import pytest

from nexar.models import Ban, Challenges, Objective, Objectives


class TestMatchModels:
    """Test match-related models."""

    @pytest.mark.skip(
        reason="Requires specific match ID - implement when match history endpoint is added"
    )
    def test_match_from_api_response(self):
        """Test Match creation from real API response."""
        # TODO: Implement when we add match history endpoints to get real match IDs
        pass

    def test_ban_creation(self):
        """Test Ban model can be created directly."""
        ban = Ban(champion_id=238, pick_turn=1)

        assert ban.champion_id == 238
        assert ban.pick_turn == 1

    def test_objective_creation(self):
        """Test Objective model can be created directly."""
        objective = Objective(first=True, kills=1)

        assert objective.first is True
        assert objective.kills == 1

    def test_challenges_creation(self):
        """Test Challenges creation from API response."""
        challenges_data = {
            "kda": 6.5,
            "killParticipation": 0.65,
            "damagePerMinute": 833.33,
            "goldPerMinute": 500.0,
            "visionScorePerMinute": 1.5,
        }

        challenges = Challenges.from_api_response(challenges_data)

        assert challenges.kda == 6.5
        assert challenges.kill_participation == 0.65
        assert challenges.damage_per_minute == 833.33
        assert challenges.gold_per_minute == 500.0
        assert challenges.vision_score_per_minute == 1.5

    def test_objectives_creation(self):
        """Test Objectives creation from API response."""
        objectives_data = {
            "baron": {"first": True, "kills": 1},
            "champion": {"first": True, "kills": 20},
            "dragon": {"first": True, "kills": 3},
            "horde": {"first": False, "kills": 0},
            "inhibitor": {"first": True, "kills": 2},
            "riftHerald": {"first": True, "kills": 1},
            "tower": {"first": True, "kills": 8},
        }

        objectives = Objectives.from_api_response(objectives_data)

        assert isinstance(objectives, Objectives)
        assert isinstance(objectives.baron, Objective)
        assert isinstance(objectives.dragon, Objective)
        assert isinstance(objectives.tower, Objective)

        # Test baron objective
        assert objectives.baron.first is True
        assert objectives.baron.kills == 1
