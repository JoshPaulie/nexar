"""Enums for regions and other constants."""

from enum import Enum


class RegionV4(Enum):
    """Regional routing values for platform-specific endpoints."""

    BR1 = "br1"
    EUN1 = "eun1"
    EUW1 = "euw1"
    JP1 = "jp1"
    KR = "kr"
    LA1 = "la1"
    LA2 = "la2"
    NA1 = "na1"
    OC1 = "oc1"
    PH2 = "ph2"
    RU = "ru"
    SG2 = "sg2"
    TH2 = "th2"
    TR1 = "tr1"
    TW2 = "tw2"
    VN2 = "vn2"


class RegionV5(Enum):
    """Regional routing values for regional endpoints."""

    AMERICAS = "americas"
    ASIA = "asia"
    EUROPE = "europe"
    SEA = "sea"


class Queue(Enum):
    """Queue types for ranked games."""

    RANKED_SOLO_5x5 = "RANKED_SOLO_5x5"
    RANKED_FLEX_SR = "RANKED_FLEX_SR"
    RANKED_FLEX_TT = "RANKED_FLEX_TT"


class Tier(Enum):
    """Ranked tiers."""

    IRON = "IRON"
    BRONZE = "BRONZE"
    SILVER = "SILVER"
    GOLD = "GOLD"
    PLATINUM = "PLATINUM"
    EMERALD = "EMERALD"
    DIAMOND = "DIAMOND"
    MASTER = "MASTER"
    GRANDMASTER = "GRANDMASTER"
    CHALLENGER = "CHALLENGER"


class Division(Enum):
    """Ranked divisions."""

    ONE = "I"
    TWO = "II"
    THREE = "III"
    FOUR = "IV"


class QueueId(Enum):
    """Queue IDs for different game modes."""

    RANKED_SOLO_5x5 = 420
    RANKED_FLEX_SR = 440
    BLIND_PICK = 430
    DRAFT_PICK = 400
    ARAM = 450
    CLASH = 700
    BOT_INTERMEDIATE = 830
    BOT_INTRO = 840
    BOT_BEGINNER = 850


class MatchType(Enum):
    """Match types for filtering match lists."""

    RANKED = "ranked"
    NORMAL = "normal"
    TOURNEY = "tourney"
    TUTORIAL = "tutorial"
