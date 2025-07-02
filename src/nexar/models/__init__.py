"""Domain models for Riot API responses."""

from .account import RiotAccount, Summoner
from .match import (
    Ban,
    Challenges,
    Match,
    MatchInfo,
    MatchMetadata,
    Missions,
    Objective,
    Objectives,
    Participant,
    Perks,
    PerkStats,
    PerkStyle,
    PerkStyleSelection,
    Team,
    TeamInfo,
    TeamsInfo,
)

__all__ = [
    # Account models
    "RiotAccount",
    "Summoner",
    # Match models
    "Match",
    "MatchInfo",
    "MatchMetadata",
    # Participant models
    "Participant",
    # Perk models
    "Perks",
    "PerkStats",
    "PerkStyle",
    "PerkStyleSelection",
    # Team models
    "Ban",
    "Objective",
    "Objectives",
    "Team",
    "TeamInfo",
    "TeamsInfo",
    # Challenge models
    "Challenges",
    "Missions",
]
