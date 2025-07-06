"""Test configuration and fixtures."""

import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio

from nexar import NexarClient, RegionV4, RegionV5


@pytest.fixture
def riot_api_key() -> str:
    """Get Riot API key from environment."""
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        pytest.skip(
            "RIOT_API_KEY environment variable not set. Source riot-key.sh before running tests.",
        )
    return api_key


@pytest_asyncio.fixture
async def async_client(riot_api_key: str) -> AsyncGenerator[NexarClient]:
    """Create a test client with real API key."""
    client = NexarClient(
        riot_api_key=riot_api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
    )
    yield client
    await client.close()


# Backward compatibility alias
@pytest_asyncio.fixture
async def client(riot_api_key: str) -> AsyncGenerator[NexarClient]:
    """Create a test client with real API key (backward compatibility)."""
    client = NexarClient(
        riot_api_key=riot_api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
    )
    yield client
    await client.close()
