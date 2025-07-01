"""Tests for match models."""

from nexar.models import (
    Ban,
    Challenges,
    Match,
    MatchInfo,
    MatchMetadata,
    Objective,
    Objectives,
    Participant,
    Perks,
    Team,
)


class TestMatchModels:
    """Test match-related models."""

    def test_match_from_api_response(self, mock_match_response):
        """Test Match creation from API response."""
        match = Match.from_api_response(mock_match_response)

        assert isinstance(match, Match)
        assert isinstance(match.metadata, MatchMetadata)
        assert isinstance(match.info, MatchInfo)

        # Test metadata
        assert match.metadata.match_id == "NA1_4567890123"
        assert match.metadata.data_version == "2"
        assert len(match.metadata.participants) == 10

        # Test info
        assert match.info.game_mode == "CLASSIC"
        assert match.info.queue_id == 420
        assert match.info.game_duration == 1800

    def test_participant_from_api_response(self, mock_match_response):
        """Test Participant creation from API response."""
        participant_data = mock_match_response["info"]["participants"][0]
        participant = Participant.from_api_response(participant_data)

        assert isinstance(participant, Participant)
        assert participant.puuid == "test-puuid-1"
        assert participant.champion_name == "Annie"
        assert participant.kills == 5
        assert participant.deaths == 2
        assert participant.assists == 8
        assert participant.win is True

        # Test nested objects
        assert isinstance(participant.perks, Perks)
        assert isinstance(participant.challenges, Challenges)

    def test_challenges_from_api_response(self):
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

    def test_team_from_api_response(self, mock_match_response):
        """Test Team creation from API response."""
        team_data = mock_match_response["info"]["teams"][0]
        team = Team.from_api_response(team_data)

        assert isinstance(team, Team)
        assert team.team_id == 100
        assert team.win is True
        assert len(team.bans) == 1
        assert isinstance(team.objectives, Objectives)

        # Test ban
        ban = team.bans[0]
        assert isinstance(ban, Ban)
        assert ban.champion_id == 238
        assert ban.pick_turn == 1

    def test_objectives_from_api_response(self, mock_match_response):
        """Test Objectives creation from API response."""
        objectives_data = mock_match_response["info"]["teams"][0]["objectives"]
        objectives = Objectives.from_api_response(objectives_data)

        assert isinstance(objectives, Objectives)
        assert isinstance(objectives.baron, Objective)
        assert isinstance(objectives.dragon, Objective)
        assert isinstance(objectives.tower, Objective)

        # Test baron objective
        assert objectives.baron.first is True
        assert objectives.baron.kills == 1
