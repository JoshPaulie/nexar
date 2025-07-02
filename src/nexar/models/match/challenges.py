"""Challenge and mission-related models."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Challenges:
    """Represents participant challenges."""

    # Core challenge stats
    kda: float | None = None
    kill_participation: float | None = None
    damage_per_minute: float | None = None
    gold_per_minute: float | None = None
    vision_score_per_minute: float | None = None

    # Additional challenge fields can be added as needed
    # Using flexible approach since challenges have many optional fields

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Challenges":
        """Create Challenges from API response."""
        return cls(
            kda=data.get("kda"),
            kill_participation=data.get("killParticipation"),
            damage_per_minute=data.get("damagePerMinute"),
            gold_per_minute=data.get("goldPerMinute"),
            vision_score_per_minute=data.get("visionScorePerMinute"),
        )


@dataclass(frozen=True)
class Missions:
    """Represents participant missions."""

    player_score_0: int | None = None
    player_score_1: int | None = None
    player_score_2: int | None = None
    player_score_3: int | None = None
    player_score_4: int | None = None
    player_score_5: int | None = None
    player_score_6: int | None = None
    player_score_7: int | None = None
    player_score_8: int | None = None
    player_score_9: int | None = None
    player_score_10: int | None = None
    player_score_11: int | None = None

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Missions":
        """Create Missions from API response."""
        return cls(
            player_score_0=data.get("playerScore0"),
            player_score_1=data.get("playerScore1"),
            player_score_2=data.get("playerScore2"),
            player_score_3=data.get("playerScore3"),
            player_score_4=data.get("playerScore4"),
            player_score_5=data.get("playerScore5"),
            player_score_6=data.get("playerScore6"),
            player_score_7=data.get("playerScore7"),
            player_score_8=data.get("playerScore8"),
            player_score_9=data.get("playerScore9"),
            player_score_10=data.get("playerScore10"),
            player_score_11=data.get("playerScore11"),
        )
