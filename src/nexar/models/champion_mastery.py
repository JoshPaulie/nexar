"""Champion mastery models."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class RewardConfig:
    """Reward configuration for a champion mastery milestone."""

    reward_value: str
    """Reward value (e.g. a chest or emote identifier)."""

    reward_type: str
    """Reward type."""

    maximum_reward: int
    """Maximum reward."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "RewardConfig":
        """Create RewardConfig from API response."""
        return cls(
            reward_value=data.get("rewardValue", ""),
            reward_type=data.get("rewardType", ""),
            maximum_reward=data.get("maximumReward", 0),
        )


@dataclass(frozen=True)
class NextSeasonMilestone:
    """Milestone progress and reward information for a champion."""

    require_grade_counts: dict[str, int]
    """Remaining grade requirements toward the next milestone, e.g. ``{"S-": 2}``."""

    reward_marks: int
    """Reward marks."""

    bonus: bool
    """Whether the current milestone carries a bonus."""

    reward_config: RewardConfig | None
    """Reward configuration, or None when Riot omits it."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "NextSeasonMilestone":
        """Create NextSeasonMilestone from API response."""
        reward_config = data.get("rewardConfig")
        return cls(
            require_grade_counts=data.get("requireGradeCounts", {}),
            reward_marks=data.get("rewardMarks", 0),
            bonus=data.get("bonus", False),
            reward_config=RewardConfig.from_api_response(reward_config) if reward_config else None,
        )


@dataclass(frozen=True)
class ChampionMastery:
    """Represents a player's champion mastery for a single champion."""

    puuid: str
    """Player's universally unique identifier."""

    champion_id: int
    """Champion ID for this entry."""

    champion_level: int
    """Champion mastery level for this player and champion."""

    champion_points: int
    """Total champion points for this player and champion; they determine the level."""

    champion_points_since_last_level: int
    """Points earned since the current level was reached."""

    champion_points_until_next_level: int
    """Points needed for the next level. Zero at maximum level."""

    chest_granted: bool
    """Whether a chest has been granted for this champion in the current season."""

    tokens_earned: int
    """Tokens earned at the current level; resets when the level advances."""

    last_play_time: datetime
    """When this champion was last played by this player."""

    mark_required_for_next_level: int
    """Marks required for the next mastery milestone."""

    champion_season_milestone: int
    """Current season milestone number for this champion."""

    milestone_grades: tuple[str, ...]
    """Grades earned toward the current milestone, oldest first."""

    next_season_milestone: NextSeasonMilestone | None
    """Next milestone requirements and reward, or None when Riot omits it."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "ChampionMastery":
        """Create ChampionMastery from API response.

        Riot omits empty values (zero points, false flags, absent milestone
        state), so everything except the identity fields parses with defaults.
        """
        next_season_milestone = data.get("nextSeasonMilestone")
        return cls(
            puuid=data["puuid"],
            champion_id=data["championId"],
            champion_level=data.get("championLevel", 0),
            champion_points=data.get("championPoints", 0),
            champion_points_since_last_level=data.get("championPointsSinceLastLevel", 0),
            champion_points_until_next_level=data.get("championPointsUntilNextLevel", 0),
            chest_granted=data.get("chestGranted", False),
            tokens_earned=data.get("tokensEarned", 0),
            last_play_time=datetime.fromtimestamp(data.get("lastPlayTime", 0) / 1000, tz=UTC),
            mark_required_for_next_level=data.get("markRequiredForNextLevel", 0),
            champion_season_milestone=data.get("championSeasonMilestone", 0),
            milestone_grades=tuple(data.get("milestoneGrades", ())),
            next_season_milestone=(
                NextSeasonMilestone.from_api_response(next_season_milestone) if next_season_milestone else None
            ),
        )
