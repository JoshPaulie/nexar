"""Test the new get_match_ids_by_puuid method."""

from typing import TYPE_CHECKING

import pytest

from nexar import MatchType, Queue

if TYPE_CHECKING:
    from nexar.client import NexarClient


class TestGetMatchIdsByPuuid:
    """Test the get_match_ids_by_puuid method."""

    @pytest.fixture
    def test_puuid(self, client: "NexarClient") -> str:
        """Get PUUID for test account - using hardcoded value to reduce API calls."""
        return "0wKS4sQQTcA6mAmu_oW5rVhyxmWAXV9hZrraXnDdh8GvelgGWYM5tM7fcHw0kalBVgCl6MxOZe0bLA"

    async def test_get_match_ids_by_puuid_basic(self, client: "NexarClient", test_puuid: str) -> None:
        """Test basic functionality of get_match_ids_by_puuid."""
        result = await client.get_match_ids_by_puuid(test_puuid)

        # Should return a list of match IDs
        assert isinstance(result, list)
        # Each match ID should be a string
        for match_id in result:
            assert isinstance(match_id, str)
            # Match IDs should follow the format REGION_MATCHID
            assert "_" in match_id

    async def test_get_match_ids_by_puuid_with_count(self, client: "NexarClient", test_puuid: str) -> None:
        """Test get_match_ids_by_puuid with count parameter."""
        result = await client.get_match_ids_by_puuid(test_puuid, count=5)

        # Should return at most 5 match IDs
        assert isinstance(result, list)
        assert len(result) <= 5

    async def test_get_match_ids_by_puuid_with_queue_filter(self, client: "NexarClient", test_puuid: str) -> None:
        """Test get_match_ids_by_puuid with queue filter."""
        # Test with ARAM queue
        result = await client.get_match_ids_by_puuid(test_puuid, queue=Queue.ARAM, count=5)

        assert isinstance(result, list)
        # Each match ID should be a string
        for match_id in result:
            assert isinstance(match_id, str)

    async def test_get_match_ids_by_puuid_with_raw_queue_id(self, client: "NexarClient", test_puuid: str) -> None:
        """Test get_match_ids_by_puuid with raw queue ID instead of enum."""
        # Test with ARAM queue ID (450)
        result = await client.get_match_ids_by_puuid(test_puuid, queue=450, count=5)

        assert isinstance(result, list)

    async def test_get_match_ids_by_puuid_with_match_type(self, client: "NexarClient", test_puuid: str) -> None:
        """Test get_match_ids_by_puuid with match type filter."""
        result = await client.get_match_ids_by_puuid(
            test_puuid,
            match_type=MatchType.NORMAL,
            count=5,
        )

        assert isinstance(result, list)

    async def test_get_match_ids_by_puuid_with_raw_match_type(self, client: "NexarClient", test_puuid: str) -> None:
        """Test get_match_ids_by_puuid with raw match type string."""
        result = await client.get_match_ids_by_puuid(test_puuid, match_type="normal", count=5)

        assert isinstance(result, list)

    async def test_get_match_ids_by_puuid_count_validation(self, client: "NexarClient", test_puuid: str) -> None:
        """Test that count parameter is validated."""
        # Test invalid count > 100
        with pytest.raises(ValueError, match="count must be between 0 and 100"):
            await client.get_match_ids_by_puuid(test_puuid, count=101)

        # Test invalid count < 0
        with pytest.raises(ValueError, match="count must be between 0 and 100"):
            await client.get_match_ids_by_puuid(test_puuid, count=-1)

    async def test_get_match_ids_by_puuid_pagination(self, client: "NexarClient", test_puuid: str) -> None:
        """Test pagination with start parameter."""
        # Get first 5 matches
        first_batch = await client.get_match_ids_by_puuid(test_puuid, start=0, count=5)

        # Get next 5 matches
        second_batch = await client.get_match_ids_by_puuid(test_puuid, start=5, count=5)

        assert isinstance(first_batch, list)
        assert isinstance(second_batch, list)

        # The batches should be different (assuming the account has enough matches)
        if len(first_batch) == 5 and len(second_batch) > 0:
            assert first_batch != second_batch
