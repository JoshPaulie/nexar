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


# Alias for platform identification - same as RegionV4 but uppercase
class PlatformId(Enum):
    """Platform identifiers for match data."""

    BR1 = "BR1"
    EUN1 = "EUN1"
    EUW1 = "EUW1"
    JP1 = "JP1"
    KR = "KR"
    LA1 = "LA1"
    LA2 = "LA2"
    NA1 = "NA1"
    OC1 = "OC1"
    PH2 = "PH2"
    RU = "RU"
    SG2 = "SG2"
    TH2 = "TH2"
    TR1 = "TR1"
    TW2 = "TW2"
    VN2 = "VN2"


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


class Tier(Enum):
    """Ranked tiers (Iron, Bronze, etc.)."""

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
    """Ranked divisions. (I, II, etc.)"""

    ONE = "I"
    TWO = "II"
    THREE = "III"
    FOUR = "IV"


class QueueId(Enum):
    """
    Queue IDs for different game modes.

    Removed all deprecated ones. Leaving obscure and temp queue IDs for forward compatibility.

    Last updated: 2025-07-05
    URL: https://static.developer.riotgames.com/docs/lol/queues.json
    """

    CUSTOM = 0
    """Custom games"""

    RANKED_PREMADE = 6
    """5v5 Ranked Premade games (Game mode deprecated)"""

    DOMINION_BLIND = 16
    """5v5 Dominion Blind Pick games (Game mode deprecated)"""

    DOMINION_DRAFT = 17
    """5v5 Dominion Draft Pick games (Game mode deprecated)"""

    DOMINION_AI = 25
    """Dominion Co-op vs AI games (Game mode deprecated)"""

    TT_RANKED_TEAM = 41
    """3v3 Ranked Team games (Game mode deprecated)"""

    RANKED_TEAM = 42
    """5v5 Ranked Team games (Game mode deprecated)"""

    TEAM_BUILDER = 61
    """5v5 Team Builder games (Game mode deprecated)"""

    ARAM_AI = 67
    """ARAM Co-op vs AI games (Game mode deprecated)"""

    SNOWDOWN_1V1 = 72
    """1v1 Snowdown Showdown games"""

    SNOWDOWN_2V2 = 73
    """2v2 Snowdown Showdown games"""

    HEXAKILL_SR = 75
    """6v6 Hexakill games"""

    URF_OLD = 76
    """Ultra Rapid Fire games"""

    ONE_FOR_ALL_MIRROR = 78
    """One For All: Mirror Mode games"""

    COOP_AI_URF = 83
    """Co-op vs AI Ultra Rapid Fire games"""

    HEXAKILL_TT = 98
    """6v6 Hexakill games (Twisted Treeline)"""

    ARAM_BUTCHERS_BRIDGE = 100
    """5v5 ARAM games (Butcher's Bridge)"""

    NEMESIS = 310
    """Nemesis games"""

    BLACK_MARKET_BRAWLERS = 313
    """Black Market Brawlers games"""

    DEFINITELY_NOT_DOMINION = 317
    """Definitely Not Dominion games"""

    ALL_RANDOM = 325
    """All Random games"""

    DRAFT_PICK = 400
    """5v5 Draft Pick games"""

    RANKED_DYNAMIC = 410
    """5v5 Ranked Dynamic games (Game mode deprecated in patch 6.22)"""

    RANKED_SOLO_5x5 = 420
    """5v5 Ranked Solo games"""

    BLIND_PICK = 430
    """5v5 Blind Pick games"""

    RANKED_FLEX_SR = 440
    """5v5 Ranked Flex games"""

    ARAM = 450
    """5v5 ARAM games"""

    QUICKPLAY = 490
    """Normal (Quickplay)"""

    BLOOD_HUNT_ASSASSIN = 600
    """Blood Hunt Assassin games"""

    DARK_STAR = 610
    """Dark Star: Singularity games"""

    CLASH = 700
    """Summoner's Rift Clash games"""

    ARAM_CLASH = 720
    """ARAM Clash games"""

    TT_AI_BEGINNER = 820
    """Co-op vs. AI Beginner Bot games"""

    BOT_INTRO_NEW = 870
    """Co-op vs. AI Intro Bot games"""

    BOT_BEGINNER_NEW = 880
    """Co-op vs. AI Beginner Bot games"""

    BOT_INTERMEDIATE_NEW = 890
    """Co-op vs. AI Intermediate Bot games"""

    ARURF = 900
    """ARURF games"""

    ASCENSION = 910
    """Ascension games"""

    PORO_KING = 920
    """Legend of the Poro King games"""

    NEXUS_SIEGE = 940
    """Nexus Siege games"""

    DOOM_BOTS_VOTING = 950
    """Doom Bots Voting games"""

    DOOM_BOTS_STANDARD = 960
    """Doom Bots Standard games"""

    STAR_GUARDIAN_INVASION_NORMAL = 980
    """Star Guardian Invasion: Normal games"""

    STAR_GUARDIAN_INVASION_ONSLAUGHT = 990
    """Star Guardian Invasion: Onslaught games"""

    PROJECT_HUNTERS = 1000
    """PROJECT: Hunters games"""

    SNOW_ARURF = 1010
    """Snow ARURF games"""

    ONE_FOR_ALL = 1020
    """One for All games"""

    ODYSSEY_INTRO = 1030
    """Odyssey Extraction: Intro games"""

    ODYSSEY_CADET = 1040
    """Odyssey Extraction: Cadet games"""

    ODYSSEY_CREWMEMBER = 1050
    """Odyssey Extraction: Crewmember games"""

    ODYSSEY_CAPTAIN = 1060
    """Odyssey Extraction: Captain games"""

    ODYSSEY_ONSLAUGHT = 1070
    """Odyssey Extraction: Onslaught games"""

    TFT = 1090
    """Teamfight Tactics games"""

    TFT_RANKED = 1100
    """Ranked Teamfight Tactics games"""

    TFT_TUTORIAL = 1110
    """Teamfight Tactics Tutorial games"""

    TFT_TEST = 1111
    """Teamfight Tactics test games"""

    TFT_CHONCC_TREASURE = 1210
    """Teamfight Tactics Choncc's Treasure Mode"""

    NEXUS_BLITZ = 1300
    """Nexus Blitz games"""

    ULTIMATE_SPELLBOOK = 1400
    """Ultimate Spellbook games"""

    ARENA = 1700
    """Arena"""

    ARENA_16P = 1710
    """Arena (16 player lobby)"""

    SWARM_1P = 1810
    """Swarm Mode Games (1 player)"""

    SWARM_2P = 1820
    """Swarm Mode Games (2 players)"""

    SWARM_3P = 1830
    """Swarm Mode Games (3 players)"""

    SWARM_4P = 1840
    """Swarm Mode Games (4 players)"""

    PICK_URF = 1900
    """Pick URF games"""

    TUTORIAL_1 = 2000
    """Tutorial 1"""

    TUTORIAL_2 = 2010
    """Tutorial 2"""

    TUTORIAL_3 = 2020
    """Tutorial 3"""


class MapId(Enum):
    """
    Map IDs for different League of Legends maps.

    Last updated: 2025-07-05
    URL: https://static.developer.riotgames.com/docs/lol/maps.json
    """

    SUMMONERS_RIFT_SUMMER = 1
    """Original Summer variant"""

    SUMMONERS_RIFT_AUTUMN = 2
    """Original Autumn variant"""

    THE_PROVING_GROUNDS = 3
    """Tutorial Map"""

    TWISTED_TREELINE_ORIGINAL = 4
    """Original Version"""

    THE_CRYSTAL_SCAR = 8
    """Dominion map"""

    TWISTED_TREELINE = 10
    """Last TT map"""

    SUMMONERS_RIFT = 11
    """Current Version"""

    HOWLING_ABYSS = 12
    """ARAM map"""

    BUTCHERS_BRIDGE = 14
    """Alternate ARAM map"""

    COSMIC_RUINS = 16
    """Dark Star: Singularity map"""

    VALORAN_CITY_PARK = 18
    """Star Guardian Invasion map"""

    SUBSTRUCTURE_43 = 19
    """PROJECT: Hunters map"""

    CRASH_SITE = 20
    """Odyssey: Extraction map"""

    NEXUS_BLITZ = 21
    """Nexus Blitz map"""

    CONVERGENCE = 22
    """Teamfight Tactics map"""

    RINGS_OF_WRATH = 30
    """Arena map"""


class MatchType(Enum):
    """Match type filters for match history."""

    RANKED = "ranked"
    """Ranked matches only"""

    NORMAL = "normal"
    """Normal matches only"""

    TOURNEY = "tourney"
    """Tournament matches only"""


class MatchParticipantPosition(Enum):
    """Participant positions in League of Legends matches."""

    TOP = "TOP"
    """Top lane position"""

    JUNGLE = "JUNGLE"
    """Jungle position"""

    MIDDLE = "MIDDLE"
    """Middle lane position"""

    BOTTOM = "BOTTOM"
    """Bottom lane (ADC) position"""

    UTILITY = "UTILITY"
    """Support position"""

    INVALID = "Invalid"
    """Invalid/unknown position (legacy data or edge cases)"""

    EMPTY = ""
    """Empty position (legacy data or edge cases)"""
