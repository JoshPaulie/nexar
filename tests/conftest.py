"""Test configuration and fixtures."""

import json
import os
from collections.abc import AsyncGenerator
from pathlib import Path
from types import TracebackType
from typing import Any, cast

import pytest
import pytest_asyncio

from nexar import NexarClient, RegionV4, RegionV5


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest to run tests sequentially to avoid database locks."""
    config.option.maxfail = 1
    config.option.numprocesses = 1


@pytest.fixture(scope="session")
def mock_responses() -> dict[str, Any]:
    """Load mock responses from JSON file."""
    mock_file = Path("tests/mock_responses.json")
    return cast("dict[str, Any]", json.loads(mock_file.read_text()))


@pytest.fixture
def riot_api_key() -> str:
    """Get Riot API key from environment."""
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        pytest.skip(
            "RIOT_API_KEY environment variable not set. Source riot-key.sh before running tests.",
        )
    return api_key


class MockResponse:
    """Mock HTTP response for testing."""

    def __init__(
        self,
        json_data: dict[str, Any] | list[dict[str, Any]] | list[str],
        *,
        status: int = 200,
        from_cache: bool = False,
    ) -> None:
        self.json_data = json_data
        self.status = status
        self.from_cache = from_cache

    async def json(self) -> dict[str, Any] | list[dict[str, Any]] | list[str]:
        """Return JSON data."""
        return self.json_data

    async def __aenter__(self) -> "MockResponse":
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit."""


@pytest_asyncio.fixture
async def client(
    riot_api_key: str,
    mock_responses: dict[str, Any],
) -> AsyncGenerator[NexarClient]:
    """Create a test client with mocked HTTP responses."""

    def get_mock_response(url: str) -> MockResponse:
        """Get appropriate mock response based on URL."""
        if "/riot/account/v1/accounts/by-riot-id" in url:
            return MockResponse(mock_responses["riot_account"])
        if "/lol/summoner/v4/summoners/by-puuid" in url:
            return MockResponse(mock_responses["summoner"])
        if "/lol/match/v5/matches/by-puuid" in url and "/ids" in url:
            return MockResponse(mock_responses["match_ids"])
        if "/lol/match/v5/matches/" in url and not url.endswith("/ids"):
            return MockResponse(mock_responses["match"])
        if "/lol/league/v4/entries/by-summoner" in url:
            return MockResponse(mock_responses["league_entries"])
        # Return a default empty response for unknown endpoints
        return MockResponse({})

    nexar_client = NexarClient(
        riot_api_key=riot_api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
    )

    # Mock the _make_api_call method directly
    original_make_api_call = nexar_client._make_api_call

    async def mock_make_api_call(
        endpoint: str,
        region: RegionV4 | RegionV5,
        params: dict[str, Any] | None = None,  # noqa: ARG001
    ) -> Any:  # noqa: ANN401
        """Mock API call that returns predefined responses."""
        url = f"https://{region.value}.api.riotgames.com{endpoint}"
        mock_response = get_mock_response(url)
        return await mock_response.json()

    nexar_client._make_api_call = mock_make_api_call

    yield nexar_client

    # Restore original method
    nexar_client._make_api_call = original_make_api_call
    await nexar_client.close()


@pytest_asyncio.fixture
async def real_client(riot_api_key: str) -> AsyncGenerator[NexarClient]:
    """Create a test client with real API key for integration tests."""
    client = NexarClient(
        riot_api_key=riot_api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
    )
    yield client
    await client.close()
