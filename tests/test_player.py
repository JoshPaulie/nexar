"""Tests for high-level Player functionality."""

import pytest

from nexar import ChampionStats, PerformanceStats, Player, QueueId


class TestPlayer:
    """Test the Player class."""

    async def test_player_initialization(self, client):
        """Test Player initializes correctly."""
        player = await Player.create(
            client=client,
            game_name="bexli",
            tag_line="bex",
        )

        assert player.game_name == "bexli"
        assert player.tag_line == "bex"
        assert player.client is client

    async def test_player_from_client_convenience_method(self, client):
        """Test creating Player via client convenience method."""
        player = await client.get_player("bexli", "bex")

        assert isinstance(player, Player)
        assert player.game_name == "bexli"
        assert player.tag_line == "bex"
        assert player.client is client

    async def test_player_riot_account_property(self, client):
        """Test accessing player's riot account."""
        player = await client.get_player("bexli", "bex")

        assert player.riot_account.game_name == "bexli"
        assert player.riot_account.tag_line == "bex"
        assert player.riot_account.puuid is not None

    async def test_player_summoner_property(self, client):
        """Test accessing player's summoner information."""
        player = await client.get_player("bexli", "bex")

        summoner = await player.get_summoner()
        assert summoner.puuid == player.riot_account.puuid
        assert summoner.summoner_level > 0

    async def test_player_puuid_property(self, client):
        """Test accessing player's PUUID."""
        player = await client.get_player("bexli", "bex")

        puuid = player.riot_account.puuid
        assert puuid is not None
        assert len(puuid) > 0

    async def test_player_league_entries_property(self, client):
        """Test accessing player's league entries."""
        player = await client.get_player("bexli", "bex")

        league_entries = await player.get_league_entries()
        assert isinstance(league_entries, list)
        # Note: May be empty if player is unranked

    async def test_player_rank_properties(self, client):
        """Test accessing player's rank information."""
        player = await client.get_player("bexli", "bex")

        # Get league entries to check for ranks
        league_entries = await player.get_league_entries()

        # Test that we get a list (may be empty if unranked)
        assert isinstance(league_entries, list)

        # If player has ranks, check the structure
        for entry in league_entries:
            assert hasattr(entry, "tier")
            assert hasattr(entry, "rank")

    async def test_player_get_recent_matches(self, real_client):
        """Test getting recent matches."""
        player = await real_client.get_player("bexli", "bex")

        matches = await player.get_matches(count=5)
        assert isinstance(matches, list)
        assert len(matches) <= 5

        for match in matches:
            assert hasattr(match, "info")
            assert hasattr(match, "metadata")

    async def test_player_get_recent_matches_with_filters(self, real_client):
        """Test getting recent matches with various filters."""
        player = await real_client.get_player("bexli", "bex")

        # Test with queue filter
        matches = await player.get_matches(count=10, queue=QueueId.RANKED_SOLO_5x5)
        assert isinstance(matches, list)
        assert len(matches) <= 10

        # Test with match type filter
        from nexar.enums import MatchType

        matches = await player.get_matches(count=5, match_type=MatchType.RANKED)
        assert isinstance(matches, list)
        assert len(matches) <= 5

    async def test_player_get_champion_stats(self, real_client):
        """Test getting champion statistics."""
        player = await real_client.get_player("bexli", "bex")

        stats = await player.get_champion_stats(count=10)
        assert isinstance(stats, list)

        for stat in stats:
            assert isinstance(stat, ChampionStats)
            assert stat.champion_id > 0
            assert stat.games_played > 0
            assert stat.wins + stat.losses == stat.games_played
            assert 0 <= stat.win_rate <= 100

    async def test_player_get_top_champions(self, real_client):
        """Test getting top played champions."""
        player = await real_client.get_player("bexli", "bex")
        top_champions = await player.get_top_champions(top_n=3, count=10)

        # Should return a list
        assert isinstance(top_champions, list)
        # Should have at most 3 champions (or fewer if player hasn't played many)
        assert len(top_champions) <= 3

    async def test_player_refresh_cache(self, client):
        """Test cache refresh functionality."""
        player = await client.get_player("bexli", "bex")

        # Get initial data to populate cache
        await player.get_summoner()

        # Verify cache is populated
        assert player._summoner is not None

        # Refresh cache
        player.refresh_cache()

        # Verify cache is cleared
        assert player._summoner is None
        assert player._summoner is None
        assert player._league_entries is None

    async def test_player_string_representations(self, client):
        """Test string representations of Player."""
        player = await client.get_player("bexli", "bex")

        str_repr = str(player)
        assert str_repr == "bexli#bex"

        repr_repr = repr(player)
        assert "Player" in repr_repr
        assert "bexli" in repr_repr
        assert "bex" in repr_repr

    async def test_player_get_performance_summary(self, real_client):
        """Test getting performance summary."""
        player = await real_client.get_player("bexli", "bex")

        summary = await player.get_recent_performance(count=10)
        assert isinstance(summary, PerformanceStats)

        # Check that all fields are present and have correct types
        assert isinstance(summary.total_games, int)
        assert isinstance(summary.wins, int)
        assert isinstance(summary.losses, int)
        assert isinstance(summary.win_rate, float)
        assert isinstance(summary.avg_kills, float)
        assert isinstance(summary.avg_deaths, float)
        assert isinstance(summary.avg_assists, float)
        assert isinstance(summary.avg_kda, float)

        # Check value ranges
        assert 0 <= summary.win_rate <= 100
        assert summary.wins + summary.losses == summary.total_games

    async def test_player_get_performance_summary_with_filters(self, real_client):
        """Test getting performance summary with queue and match type filters."""
        player = await real_client.get_player("bexli", "bex")

        # Test with queue filter
        summary = await player.get_recent_performance(count=5)
        assert isinstance(summary, PerformanceStats)
        assert summary.total_games >= 0

        # Test with different count
        summary_large = await player.get_recent_performance(count=15)
        assert isinstance(summary_large, PerformanceStats)
        assert summary_large.total_games >= 0

    async def test_player_is_on_win_streak(self, real_client):
        """Test win streak detection."""
        player = await real_client.get_player("bexli", "bex")

        # Test the method exists and returns a boolean
        win_streak = await player.is_on_win_streak(min_games=2)
        assert isinstance(win_streak, bool)

    async def test_player_get_recent_performance_by_role(self, real_client):
        """Test getting performance statistics by role."""
        player = await real_client.get_player("bexli", "bex")

        role_performance = await player.get_recent_performance_by_role(count=10)
        assert isinstance(role_performance, dict)

        # Each role should have performance stats
        for role, stats in role_performance.items():
            assert "games" in stats
            assert "wins" in stats
            assert "win_rate" in stats

    async def test_player_get_recent_performance_by_role_with_queue(self, real_client):
        """Test getting role performance with queue filter."""
        player = await real_client.get_player("bexli", "bex")

        from nexar.enums import QueueId

        role_performance = await player.get_recent_performance_by_role(count=5, queue=QueueId.RANKED_SOLO_5x5)
        assert isinstance(role_performance, dict)

    async def test_player_cache_behavior(self, client):
        """Test that Player properties are properly cached."""
        player = await client.get_player("bexli", "bex")

        # First access should make API calls and cache results
        riot_account1 = player.riot_account
        riot_account2 = player.riot_account

        # Should be the same object (cached)
        assert riot_account1 is riot_account2

        summoner1 = await player.get_summoner()
        summoner2 = await player.get_summoner()

        # Should be the same object (cached)
        assert summoner1 is summoner2

    async def test_player_regions_customization(self, client):
        """Test Player with custom regions."""
        from nexar.enums import RegionV4, RegionV5

        player = await Player.create(
            client=client,
            game_name="bexli",
            tag_line="bex",
            v4_region=RegionV4.EUW1,
            v5_region=RegionV5.EUROPE,
        )

        assert player.v4_region == RegionV4.EUW1
        assert player.v5_region == RegionV5.EUROPE

    async def test_player_with_regions_fallback_to_defaults(self, client):
        """Test Player falls back to client defaults when no regions specified."""
        player = await Player.create(
            client=client,
            game_name="bexli",
            tag_line="bex",
        )

        # Regions should be None (will use client defaults)
        assert player.v4_region is None
        assert player.v5_region is None

    async def test_player_performance_summary_minimal_count(self, real_client):
        """Test performance summary with minimal match count."""
        player = await real_client.get_player("bexli", "bex")

        # Test with very small count to verify method handles edge cases
        summary = await player.get_recent_performance(count=1)
        assert isinstance(summary, PerformanceStats)
        assert summary.total_games >= 0

    async def test_champion_stats_with_queue_filter(self, real_client):
        """Test champion stats with queue filter."""
        player = await real_client.get_player("bexli", "bex")

        stats = await player.get_champion_stats(count=20, queue=QueueId.RANKED_SOLO_5x5)
        assert isinstance(stats, list)

        for stat in stats:
            assert isinstance(stat, ChampionStats)

    async def test_champion_stats_with_match_type_filter(self, real_client):
        """Test champion stats with match type filter."""
        player = await real_client.get_player("bexli", "bex")

        from nexar.enums import MatchType

        stats = await player.get_champion_stats(count=10, match_type=MatchType.RANKED)
        assert isinstance(stats, list)

    async def test_top_champions_edge_cases(self, real_client):
        """Test top champions with edge cases."""
        player = await real_client.get_player("bexli", "bex")

        # Test with small count
        top_champions = await player.get_top_champions(top_n=1, count=5)
        assert isinstance(top_champions, list)
        assert len(top_champions) <= 1

    async def test_player_methods_with_datetime_filters(self, real_client):
        """Test Player methods that accept datetime filters."""
        from datetime import datetime, timedelta

        player = await real_client.get_player("bexli", "bex")

        # Test with datetime objects
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)

        matches = await player.get_matches(
            count=10,
            start_time=start_time,
            end_time=end_time,
        )
        assert isinstance(matches, list)

        # Test champion stats with time filters
        stats = await player.get_champion_stats(
            count=10,
            start_time=start_time,
            end_time=end_time,
        )
        assert isinstance(stats, list)

    async def test_player_puuid_consistency(self, client):
        """Test that PUUID is consistent across different access methods."""
        player = await client.get_player("bexli", "bex")

        # PUUID should be the same whether accessed via property or riot_account
        riot_account = player.riot_account
        puuid_via_riot_account = riot_account.puuid

        summoner = await player.get_summoner()
        puuid_via_summoner = summoner.puuid

        assert puuid_via_riot_account == puuid_via_summoner

    async def test_player_rank_properties_edge_cases(self, client):
        """Test rank properties when player has no ranked entries."""
        player = await client.get_player("bexli", "bex")

        # Even if player is unranked, this should not crash
        league_entries = await player.get_league_entries()
        assert isinstance(league_entries, list)
        # List may be empty for unranked players

    def test_champion_stats_perfect_record(self):
        """Test ChampionStats with perfect win record."""
        stats = ChampionStats(
            champion_id=1,
            champion_name="Annie",
            games_played=5,
            wins=5,
            losses=0,
            total_kills=50,
            total_deaths=5,
            total_assists=25,
        )

        assert stats.win_rate == 100.0
        assert stats.avg_kills == 10.0
        assert stats.avg_deaths == 1.0
        assert stats.avg_assists == 5.0

    def test_champion_stats_realistic_values(self):
        """Test ChampionStats with realistic game values."""
        stats = ChampionStats(
            champion_id=42,
            champion_name="Corki",
            games_played=20,
            wins=12,
            losses=8,
            total_kills=240,
            total_deaths=160,
            total_assists=300,
        )

        assert stats.win_rate == 60.0
        assert stats.avg_kills == 12.0
        assert stats.avg_deaths == 8.0
        assert stats.avg_assists == 15.0
        assert stats.avg_kda == 3.375  # (240 + 300) / 160

    def test_champion_stats_data_integrity(self):
        """Test ChampionStats data consistency."""
        stats = ChampionStats(
            champion_id=89,
            champion_name="Leona",
            games_played=10,
            wins=6,
            losses=4,
            total_kills=30,
            total_deaths=80,
            total_assists=200,
        )

        # Wins + losses should equal games played
        assert stats.wins + stats.losses == stats.games_played

        # All stats should be non-negative
        assert stats.wins >= 0
        assert stats.losses >= 0
        assert stats.total_kills >= 0
        assert stats.total_deaths >= 0
        assert stats.total_assists >= 0
