"""Test configuration and fixtures."""

import os

import pytest

from nexar import NexarClient, RegionV4, RegionV5


@pytest.fixture
def riot_api_key():
    """Get Riot API key from environment."""
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        pytest.skip(
            "RIOT_API_KEY environment variable not set. Source riot-key.sh before running tests.",
        )
    return api_key


@pytest.fixture
def client(riot_api_key):
    """Create a test client with real API key."""
    return NexarClient(
        riot_api_key=riot_api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
    )
