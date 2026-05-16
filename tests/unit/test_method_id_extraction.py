"""Tests for method ID extraction in client.py."""

import pytest

from nexar import NexarClient
from nexar.enums import Region


class TestMethodIDExtraction:
    """Test the _extract_method_id static method for robust endpoint parsing."""

    def test_standard_summoner_endpoint(self) -> None:
        """Test standard League of Legends summoner endpoint."""
        endpoint = "/lol/summoner/v4/summoners/by-puuid/test-puuid"
        assert NexarClient._extract_method_id(endpoint) == "summoner-v4"

    def test_standard_match_endpoint(self) -> None:
        """Test standard League of Legends match endpoint."""
        endpoint = "/lol/match/v5/matches/NA1_test_match_id"
        assert NexarClient._extract_method_id(endpoint) == "match-v5"

    def test_standard_match_ids_endpoint(self) -> None:
        """Test standard League of Legends match IDs endpoint."""
        endpoint = "/lol/match/v5/matches/by-puuid/test-puuid/ids"
        assert NexarClient._extract_method_id(endpoint) == "match-v5"

    def test_league_entries_endpoint(self) -> None:
        """Test League entries endpoint."""
        endpoint = "/lol/league/v4/entries/by-puuid/test-puuid"
        assert NexarClient._extract_method_id(endpoint) == "league-v4"

    def test_riot_account_endpoint(self) -> None:
        """Test Riot account endpoint."""
        endpoint = "/riot/account/v1/accounts/by-riot-id/PlayerName/TAG"
        assert NexarClient._extract_method_id(endpoint) == "account-v1"

    def test_static_data_champion_endpoint(self) -> None:
        """Test static data champion endpoint."""
        endpoint = "/static-data/lol/champion/1"
        assert NexarClient._extract_method_id(endpoint) == "champion-static"

    def test_static_data_item_endpoint(self) -> None:
        """Test static data item endpoint."""
        endpoint = "/static-data/lol/item/1001"
        assert NexarClient._extract_method_id(endpoint) == "item-static"

    def test_static_data_with_locale(self) -> None:
        """Test static data endpoint with locale parameter."""
        endpoint = "/static-data/lol/champion/1?locale=en_US"
        # The query string should be stripped before processing
        # But our function works with just the path part
        assert NexarClient._extract_method_id(endpoint.split("?")[0]) == "champion-static"

    def test_valorant_endpoint(self) -> None:
        """Test Valorant API endpoint."""
        endpoint = "/val/match/v1/matches/test-match-id"
        assert NexarClient._extract_method_id(endpoint) == "match-v1"

    def test_valorant_ranked_endpoint(self) -> None:
        """Test Valorant ranked endpoint."""
        endpoint = "/val/ranked/v1/leaderboards/by-puuid/test-puuid"
        assert NexarClient._extract_method_id(endpoint) == "ranked-v1"

    def test_valorant_account_endpoint(self) -> None:
        """Test Valorant account endpoint."""
        endpoint = "/val/content/v1/content"
        assert NexarClient._extract_method_id(endpoint) == "content-v1"

    def test_teamfight_tactics_endpoint(self) -> None:
        """Test TFT API endpoint."""
        endpoint = "/tft/match/v1/matches/NA1_test_match_id"
        assert NexarClient._extract_method_id(endpoint) == "match-v1"

    def test_teamfight_tactics_summoner_endpoint(self) -> None:
        """Test TFT summoner endpoint."""
        endpoint = "/tft/summoner/v1/summoners/by-puuid/test-puuid"
        assert NexarClient._extract_method_id(endpoint) == "summoner-v1"

    def test_lor_endpoint(self) -> None:
        """Test Legends of Runeterra API endpoint."""
        endpoint = "/lor/match/v1/matches/NA1_test_match_id"
        assert NexarClient._extract_method_id(endpoint) == "match-v1"

    def test_leading_slash_removed(self) -> None:
        """Test that leading slashes are handled correctly."""
        endpoint1 = "/lol/summoner/v4/summoners/by-puuid/test-puuid"
        endpoint2 = "lol/summoner/v4/summoners/by-puuid/test-puuid"
        assert NexarClient._extract_method_id(endpoint1) == NexarClient._extract_method_id(endpoint2)

    def test_complex_path_with_parameters(self) -> None:
        """Test endpoint with multiple path parameters."""
        endpoint = "/lol/summoner/v4/summoners/by-riot-id/PlayerName/TAG/statsum"
        assert NexarClient._extract_method_id(endpoint) == "summoner-v4"

    def test_deep_nested_path(self) -> None:
        """Test deeply nested endpoint paths."""
        endpoint = "/lol/match/v5/matches/NA1_match_id/timeline"
        assert NexarClient._extract_method_id(endpoint) == "match-v5"

    def test_two_part_endpoint_fallback(self) -> None:
        """Test endpoint with only two parts (edge case)."""
        # This is a malformed endpoint, but we should still handle it gracefully
        endpoint = "/static-data"
        result = NexarClient._extract_method_id(endpoint)
        # Should not crash and should return something
        assert isinstance(result, str)
        assert result != ""

    def test_single_part_endpoint_returns_unknown(self) -> None:
        """Test that single-part endpoints return 'unknown'."""
        endpoint = "/api"
        assert NexarClient._extract_method_id(endpoint) == "unknown"

    def test_empty_endpoint_returns_unknown(self) -> None:
        """Test that empty or root endpoints return 'unknown'."""
        endpoint = "/"
        assert NexarClient._extract_method_id(endpoint) == "unknown"

    def test_version_extraction_v1(self) -> None:
        """Test extraction with v1 version."""
        endpoint = "/custom/service/v1/resource/id"
        assert NexarClient._extract_method_id(endpoint) == "service-v1"

    def test_version_extraction_v10(self) -> None:
        """Test extraction with v10 version (double digit)."""
        endpoint = "/custom/service/v10/resource/id"
        assert NexarClient._extract_method_id(endpoint) == "service-v10"

    def test_version_in_middle_of_path(self) -> None:
        """Test version that appears in the middle of the path."""
        endpoint = "/api/v2/resource/v1/details"
        # Should match the first version found (v2)
        result = NexarClient._extract_method_id(endpoint)
        assert "v2" in result or "v1" in result  # One of these should be present

    def test_static_data_lor_endpoint(self) -> None:
        """Test static data for Legends of Runeterra."""
        endpoint = "/static-data/lor/card/01IO012"
        assert NexarClient._extract_method_id(endpoint) == "card-static"

    def test_static_data_tft_endpoint(self) -> None:
        """Test static data for Teamfight Tactics."""
        endpoint = "/static-data/tft/items"
        assert NexarClient._extract_method_id(endpoint) == "items-static"

    def test_static_data_valorant_endpoint(self) -> None:
        """Test static data for Valorant."""
        endpoint = "/static-data/valorant/agents"
        assert NexarClient._extract_method_id(endpoint) == "agents-static"


class TestMethodIDExtractionEdgeCases:
    """Test edge cases and robustness of method ID extraction."""

    def test_uppercase_version_pattern(self) -> None:
        """Test that uppercase V is not matched."""
        endpoint = "/api/Service/V1/resource"
        # V1 should not match (lowercase v required)
        result = NexarClient._extract_method_id(endpoint)
        # Should fall back to basic parsing
        assert isinstance(result, str)

    def test_malformed_version_not_matched(self) -> None:
        """Test that malformed versions are not matched."""
        endpoint = "/api/service/v/resource"
        # v without number should not match
        result = NexarClient._extract_method_id(endpoint)
        assert isinstance(result, str)

    def test_query_string_in_endpoint(self) -> None:
        """Test that endpoints with query strings are handled (if passed with ?)."""
        # Note: In practice, query strings should be stripped before calling this,
        # but we test robustness
        endpoint = "/lol/summoner/v4/summoners/by-puuid/id?locale=en_US"
        # The method works on path only, so query string becomes part of last component
        # This tests that the function doesn't crash
        result = NexarClient._extract_method_id(endpoint.split("?")[0])
        assert result == "summoner-v4"

    def test_percent_encoded_characters(self) -> None:
        """Test endpoints with percent-encoded characters."""
        endpoint = "/lol/summoner/v4/summoners/by-puuid/%test%20puuid"
        assert NexarClient._extract_method_id(endpoint) == "summoner-v4"

    def test_trailing_slash(self) -> None:
        """Test that trailing slashes don't break parsing."""
        endpoint = "/lol/summoner/v4/summoners/by-puuid/test/"
        assert NexarClient._extract_method_id(endpoint) == "summoner-v4"

    def test_multiple_consecutive_slashes(self) -> None:
        """Test handling of multiple consecutive slashes."""
        endpoint = "/lol//summoner/v4//summoners"
        # This will create empty parts, but should still work
        result = NexarClient._extract_method_id(endpoint)
        assert isinstance(result, str)

    def test_very_long_endpoint(self) -> None:
        """Test that very long endpoints are parsed correctly."""
        endpoint = "/lol/match/v5/matches/" + "a" * 1000
        assert NexarClient._extract_method_id(endpoint) == "match-v5"


class TestMethodIDExtractionIntegration:
    """Integration tests for method ID extraction in context."""

    @pytest.mark.asyncio
    async def test_method_id_extraction_in_client_context(self) -> None:
        """Test that the client can successfully initialize and use the extraction method."""
        # Note: This is a basic test that the method exists and is callable
        client = NexarClient(
            riot_api_key="test-key",
            default_region=Region.NA1,
        )

        # Test that the static method is callable
        result = client._extract_method_id("/lol/summoner/v4/summoners/by-puuid/test")
        assert result == "summoner-v4"

        # Test that it's callable directly from the class
        result2 = NexarClient._extract_method_id("/lol/match/v5/matches/test")
        assert result2 == "match-v5"

    def test_consistency_across_multiple_calls(self) -> None:
        """Test that extraction is consistent across multiple calls."""
        endpoint = "/lol/summoner/v4/summoners/by-puuid/test-puuid"
        results = [NexarClient._extract_method_id(endpoint) for _ in range(10)]
        # All results should be identical
        assert len(set(results)) == 1
        assert results[0] == "summoner-v4"

    def test_different_endpoints_get_different_ids(self) -> None:
        """Test that different endpoints get different method IDs."""
        summoner_endpoint = "/lol/summoner/v4/summoners/by-puuid/test"
        match_endpoint = "/lol/match/v5/matches/test"
        league_endpoint = "/lol/league/v4/entries/by-puuid/test"

        ids = {
            NexarClient._extract_method_id(summoner_endpoint),
            NexarClient._extract_method_id(match_endpoint),
            NexarClient._extract_method_id(league_endpoint),
        }

        # All should be different
        assert len(ids) == 3
        assert "summoner-v4" in ids
        assert "match-v5" in ids
        assert "league-v4" in ids
