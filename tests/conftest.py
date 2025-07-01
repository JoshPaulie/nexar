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
def requests_mock_obj():
    """Requests mock object for testing."""
    with requests_mock.Mocker() as m:
        yield m
