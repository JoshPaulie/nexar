"""Test configuration and fixtures."""

import pytest
import requests_mock

from nexar import NexarClient, RegionV4, RegionV5


@pytest.fixture
def mock_api_key():
    """Mock API key for testing."""
    return "RGAPI-test-key-123"


@pytest.fixture
def client(mock_api_key):
    """Create a test client."""
    return NexarClient(
        riot_api_key=mock_api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
    )


@pytest.fixture
def mock_riot_account_response():
    """Mock response for riot account endpoint."""
    return {"puuid": "test-puuid-123", "gameName": "TestPlayer", "tagLine": "TEST"}


@pytest.fixture
def mock_summoner_response():
    """Mock response for summoner endpoint."""
    return {
        "id": "test-summoner-id",
        "puuid": "test-puuid-123",
        "profileIconId": 1234,
        "revisionDate": 1609459200000,
        "summonerLevel": 150,
    }


@pytest.fixture
def mock_match_response():
    """Mock response for match endpoint."""
    return {
        "metadata": {
            "dataVersion": "2",
            "matchId": "NA1_4567890123",
            "participants": [
                "test-puuid-1",
                "test-puuid-2",
                "test-puuid-3",
                "test-puuid-4",
                "test-puuid-5",
                "test-puuid-6",
                "test-puuid-7",
                "test-puuid-8",
                "test-puuid-9",
                "test-puuid-10",
            ],
        },
        "info": {
            "gameCreation": 1609459200000,
            "gameDuration": 1800,
            "gameId": 4567890123,
            "gameMode": "CLASSIC",
            "gameStartTimestamp": 1609459300000,
            "gameType": "MATCHED_GAME",
            "gameVersion": "11.1.354.9229",
            "mapId": 11,
            "platformId": "NA1",
            "queueId": 420,
            "participants": [
                {
                    "puuid": "test-puuid-1",
                    "summonerName": "TestPlayer1",
                    "championId": 1,
                    "championName": "Annie",
                    "teamId": 100,
                    "participantId": 1,
                    "kills": 5,
                    "deaths": 2,
                    "assists": 8,
                    "champLevel": 18,
                    "goldEarned": 15000,
                    "goldSpent": 14500,
                    "totalDamageDealtToChampions": 25000,
                    "totalDamageTaken": 18000,
                    "visionScore": 45,
                    "item0": 6653,
                    "item1": 3020,
                    "item2": 3157,
                    "item3": 3135,
                    "item4": 3089,
                    "item5": 3916,
                    "item6": 3364,
                    "individualPosition": "MIDDLE",
                    "teamPosition": "MIDDLE",
                    "lane": "MIDDLE",
                    "role": "SOLO",
                    "win": True,
                    "perks": {
                        "statPerks": {"defense": 5002, "flex": 5008, "offense": 5005},
                        "styles": [
                            {
                                "description": "primaryStyle",
                                "selections": [
                                    {"perk": 8112, "var1": 1606, "var2": 0, "var3": 0}
                                ],
                                "style": 8100,
                            }
                        ],
                    },
                    "challenges": {
                        "kda": 6.5,
                        "killParticipation": 0.65,
                        "damagePerMinute": 833.33,
                        "goldPerMinute": 500.0,
                        "visionScorePerMinute": 1.5,
                    },
                }
            ],
            "teams": [
                {
                    "teamId": 100,
                    "win": True,
                    "bans": [{"championId": 238, "pickTurn": 1}],
                    "objectives": {
                        "baron": {"first": True, "kills": 1},
                        "champion": {"first": True, "kills": 20},
                        "dragon": {"first": True, "kills": 3},
                        "horde": {"first": False, "kills": 0},
                        "inhibitor": {"first": True, "kills": 2},
                        "riftHerald": {"first": True, "kills": 1},
                        "tower": {"first": True, "kills": 8},
                    },
                }
            ],
        },
    }


@pytest.fixture
def requests_mock_obj():
    """Requests mock object for testing."""
    with requests_mock.Mocker() as m:
        yield m
