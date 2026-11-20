"""Domain models for Riot API responses."""

from .account import RiotAccount, Summoner
from .champion_mastery import ChampionMastery, NextSeasonMilestone, RewardConfig
from .league import LeagueEntry, MiniSeries
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
    ParticipantList,
    Perks,
    PerkStats,
    PerkStyle,
    PerkStyleSelection,
    Team,
)
from .player import Player
from .stats import ChampionStats, PerformanceStats

__all__ = [
    "Ban",
    "Challenges",
    "ChampionMastery",
    "ChampionStats",
    "LeagueEntry",
    "Match",
    "MatchInfo",
    "MatchMetadata",
    "MiniSeries",
    "Missions",
    "NextSeasonMilestone",
    "Objective",
    "Objectives",
    "Participant",
    "ParticipantList",
    "PerformanceStats",
    "PerkStats",
    "PerkStyle",
    "PerkStyleSelection",
    "Perks",
    "Player",
    "RewardConfig",
    "RiotAccount",
    "Summoner",
    "Team",
]
