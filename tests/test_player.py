"""Tests for high-level Player functionality."""

from nexar import ChampionStats, Player, QueueId


class TestPlayer:
    """Test the Player class."""

    def test_player_initialization(self, client):
        """Test Player initializes correctly."""
        player = Player(
            client=client,
            game_name="bexli",
            tag_line="bex",
        )

        assert player.game_name == "bexli"
        assert player.tag_line == "bex"
        assert player._client is client

    def test_player_from_client_convenience_method(self, client):
        """Test creating Player via client convenience method."""
        player = client.get_player("bexli", "bex")

        assert isinstance(player, Player)
        assert player.game_name == "bexli"
        assert player.tag_line == "bex"
        assert player._client is client

    def test_player_riot_account_property(self, client):
        """Test accessing player's riot account."""
        player = client.get_player("bexli", "bex")

        riot_account = player.riot_account
        assert riot_account.game_name == "bexli"
        assert riot_account.tag_line == "bex"
        assert riot_account.puuid is not None

    def test_player_summoner_property(self, client):
        """Test accessing player's summoner information."""
        player = client.get_player("bexli", "bex")

        summoner = player.summoner
        assert summoner.puuid == player.puuid
        assert summoner.summoner_level > 0

    def test_player_puuid_property(self, client):
        """Test accessing player's PUUID."""
        player = client.get_player("bexli", "bex")

        puuid = player.puuid
        assert puuid is not None
        assert len(puuid) > 0

    def test_player_league_entries_property(self, client):
        """Test accessing player's league entries."""
        player = client.get_player("bexli", "bex")

        league_entries = player.league_entries
        assert isinstance(league_entries, list)
        # Note: May be empty if player is unranked

    def test_player_rank_properties(self, client):
        """Test accessing player's rank information."""
        player = client.get_player("bexli", "bex")

        # These may be None if the player is unranked
        solo_rank = player.rank
        flex_rank = player.flex_rank

        # Just test that they return the expected types
        assert solo_rank is None or hasattr(solo_rank, "tier")
        assert flex_rank is None or hasattr(flex_rank, "tier")

    def test_player_get_recent_matches(self, client):
        """Test getting recent matches."""
        player = client.get_player("bexli", "bex")

        matches = player.get_recent_matches(count=5)
        assert isinstance(matches, list)
        assert len(matches) <= 5

        for match in matches:
            assert hasattr(match, "info")
            assert hasattr(match, "metadata")

    def test_player_get_recent_matches_with_filters(self, client):
        """Test getting recent matches with various filters."""
        player = client.get_player("bexli", "bex")

        # Test with queue filter
        matches = player.get_recent_matches(count=10, queue=QueueId.RANKED_SOLO_5x5)
        assert isinstance(matches, list)
        assert len(matches) <= 10

        # Test with match type filter
        from nexar.enums import MatchType

        matches = player.get_recent_matches(count=5, match_type=MatchType.RANKED)
        assert isinstance(matches, list)
        assert len(matches) <= 5

    def test_player_get_champion_stats(self, client):
        """Test getting champion statistics."""
        player = client.get_player("bexli", "bex")

        stats = player.get_champion_stats(count=10)
        assert isinstance(stats, list)

        for stat in stats:
            assert isinstance(stat, ChampionStats)
            assert stat.champion_id > 0
            assert stat.games_played > 0
            assert stat.wins + stat.losses == stat.games_played
            assert 0 <= stat.win_rate <= 100

    def test_player_get_top_champions(self, client):
        """Test getting top played champions."""
        player = client.get_player("bexli", "bex")

        top_champs = player.get_top_champions(top_n=3, count=20)
        assert isinstance(top_champs, list)
        assert len(top_champs) <= 3

        # Should be sorted by games played (descending)
        for i in range(1, len(top_champs)):
            assert top_champs[i - 1].games_played >= top_champs[i].games_played

    def test_player_refresh_cache(self, client):
        """Test cache refresh functionality."""
        player = client.get_player("bexli", "bex")

        # Access properties to populate cache
        _ = player.riot_account
        _ = player.summoner
        _ = player.league_entries

        # Verify cache is populated
        assert player._riot_account is not None
        assert player._summoner is not None
        assert player._league_entries is not None

        # Refresh cache
        player.refresh_cache()

        # Verify cache is cleared
        assert player._riot_account is None
        assert player._summoner is None
        assert player._league_entries is None

    def test_player_string_representations(self, client):
        """Test string representations of Player."""
        player = client.get_player("bexli", "bex")

        str_repr = str(player)
        assert "bexli#bex" in str_repr

        repr_str = repr(player)
        assert "bexli" in repr_str
        assert "bex" in repr_str

    def test_player_get_performance_summary(self, client):
        """Test getting performance summary."""
        player = client.get_player("bexli", "bex")

        summary = player.get_performance_summary(count=10)
        assert isinstance(summary, dict)

        # Check required keys
        required_keys = [
            "total_games",
            "wins",
            "losses",
            "win_rate",
            "avg_kills",
            "avg_deaths",
            "avg_assists",
            "avg_kda",
            "avg_cs",
            "avg_game_duration_minutes",
        ]
        for key in required_keys:
            assert key in summary

        # Check data types and logical constraints
        assert isinstance(summary["total_games"], int)
        assert isinstance(summary["wins"], int)
        assert isinstance(summary["losses"], int)
        assert summary["wins"] + summary["losses"] == summary["total_games"]
        assert 0 <= summary["win_rate"] <= 100
        assert summary["avg_kills"] >= 0
        assert summary["avg_deaths"] >= 0
        assert summary["avg_assists"] >= 0
        assert summary["avg_kda"] >= 0
        assert summary["avg_cs"] >= 0
        assert summary["avg_game_duration_minutes"] >= 0

    def test_player_get_performance_summary_with_filters(self, client):
        """Test getting performance summary with queue and match type filters."""
        player = client.get_player("bexli", "bex")

        # Test with queue filter
        summary = player.get_performance_summary(count=5, queue=QueueId.RANKED_SOLO_5x5)
        assert isinstance(summary, dict)
        assert "total_games" in summary

        # Test with match type filter
        from nexar.enums import MatchType

        summary = player.get_performance_summary(count=5, match_type=MatchType.RANKED)
        assert isinstance(summary, dict)
        assert "total_games" in summary

    def test_player_is_on_win_streak(self, client):
        """Test win streak detection."""
        player = client.get_player("bexli", "bex")

        # Test with default min_games (3)
        streak = player.is_on_win_streak()
        assert isinstance(streak, bool)

        # Test with custom min_games
        streak = player.is_on_win_streak(min_games=2)
        assert isinstance(streak, bool)

        streak = player.is_on_win_streak(min_games=5)
        assert isinstance(streak, bool)

    def test_player_get_recent_performance_by_role(self, client):
        """Test getting performance statistics by role."""
        player = client.get_player("bexli", "bex")

        role_stats = player.get_recent_performance_by_role(count=20)
        assert isinstance(role_stats, dict)

        # Each role should have complete stats
        for role, stats in role_stats.items():
            assert isinstance(role, str)
            assert isinstance(stats, dict)

            required_keys = [
                "games_played",
                "wins",
                "total_kills",
                "total_deaths",
                "total_assists",
                "total_cs",
                "win_rate",
                "avg_kills",
                "avg_deaths",
                "avg_assists",
                "avg_cs",
                "avg_kda",
            ]
            for key in required_keys:
                assert key in stats

            # Check logical constraints
            assert stats["games_played"] > 0
            assert stats["wins"] <= stats["games_played"]
            assert 0 <= stats["win_rate"] <= 100
            assert stats["avg_kills"] >= 0
            assert stats["avg_deaths"] >= 0
            assert stats["avg_assists"] >= 0
            assert stats["avg_cs"] >= 0
            assert stats["avg_kda"] >= 0

    def test_player_get_recent_performance_by_role_with_queue(self, client):
        """Test getting role performance with queue filter."""
        player = client.get_player("bexli", "bex")

        role_stats = player.get_recent_performance_by_role(
            count=10, queue=QueueId.RANKED_SOLO_5x5
        )
        assert isinstance(role_stats, dict)

    def test_player_cache_behavior(self, client):
        """Test that Player properties are properly cached."""
        player = client.get_player("bexli", "bex")

        # First access should make API calls and cache results
        riot_account1 = player.riot_account
        summoner1 = player.summoner
        league_entries1 = player.league_entries

        # Second access should return cached objects (same identity)
        riot_account2 = player.riot_account
        summoner2 = player.summoner
        league_entries2 = player.league_entries

        assert riot_account1 is riot_account2
        assert summoner1 is summoner2
        assert league_entries1 is league_entries2

    def test_player_regions_customization(self, client):
        """Test Player with custom regions."""
        from nexar.enums import RegionV4, RegionV5

        player = Player(
            client=client,
            game_name="bexli",
            tag_line="bex",
            v4_region=RegionV4.EUW1,
            v5_region=RegionV5.EUROPE,
        )

        assert player._v4_region == RegionV4.EUW1
        assert player._v5_region == RegionV5.EUROPE

    def test_player_with_regions_fallback_to_defaults(self, client):
        """Test that Player falls back to client defaults when regions not specified."""
        player = Player(
            client=client,
            game_name="bexli",
            tag_line="bex",
            # No regions specified
        )

        assert player._v4_region == client.default_v4_region
        assert player._v5_region == client.default_v5_region

    def test_player_performance_summary_minimal_count(self, client):
        """Test performance summary with minimal match count."""
        player = client.get_player("bexli", "bex")

        # Test with very small count to verify method handles edge cases
        summary = player.get_performance_summary(count=1)
        assert isinstance(summary, dict)
        assert "total_games" in summary
        assert summary["total_games"] >= 0

    def test_champion_stats_with_queue_filter(self, client):
        """Test champion stats with queue filter."""
        player = client.get_player("bexli", "bex")

        stats = player.get_champion_stats(count=20, queue=QueueId.RANKED_SOLO_5x5)
        assert isinstance(stats, list)

        for stat in stats:
            assert isinstance(stat, ChampionStats)

    def test_champion_stats_with_match_type_filter(self, client):
        """Test champion stats with match type filter."""
        player = client.get_player("bexli", "bex")
        from nexar.enums import MatchType

        stats = player.get_champion_stats(count=15, match_type=MatchType.RANKED)
        assert isinstance(stats, list)

    def test_top_champions_edge_cases(self, client):
        """Test top champions with edge cases."""
        player = client.get_player("bexli", "bex")

        # Request more champions than available
        top_champs = player.get_top_champions(top_n=50, count=10)
        assert isinstance(top_champs, list)
        assert len(top_champs) <= 50  # Should not exceed available

        # Request 0 champions
        top_champs = player.get_top_champions(top_n=0, count=10)
        assert isinstance(top_champs, list)
        assert len(top_champs) == 0

    def test_player_methods_with_datetime_filters(self, client):
        """Test Player methods that accept datetime filters."""
        from datetime import datetime, timedelta

        player = client.get_player("bexli", "bex")

        # Test with datetime objects
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)

        matches = player.get_recent_matches(
            count=10, start_time=start_time, end_time=end_time
        )
        assert isinstance(matches, list)

        # Test with epoch timestamps
        end_epoch = int(end_time.timestamp())
        start_epoch = int(start_time.timestamp())

        matches = player.get_recent_matches(
            count=10, start_time=start_epoch, end_time=end_epoch
        )
        assert isinstance(matches, list)

    def test_player_puuid_consistency(self, client):
        """Test that PUUID is consistent across different access methods."""
        player = client.get_player("bexli", "bex")

        # PUUID should be the same whether accessed via property or riot_account
        puuid_via_property = player.puuid
        puuid_via_account = player.riot_account.puuid
        puuid_via_summoner = player.summoner.puuid

        assert puuid_via_property == puuid_via_account
        assert puuid_via_property == puuid_via_summoner

    def test_player_rank_properties_edge_cases(self, client):
        """Test rank properties when player has no ranked entries."""
        player = client.get_player("bexli", "bex")

        # Even if player is unranked, these should not crash
        solo_rank = player.rank
        flex_rank = player.flex_rank

        # They might be None, but should be valid LeagueEntry or None
        if solo_rank is not None:
            assert hasattr(solo_rank, "tier")
            assert hasattr(solo_rank, "rank")
            assert hasattr(solo_rank, "league_points")

        if flex_rank is not None:
            assert hasattr(flex_rank, "tier")
            assert hasattr(flex_rank, "rank")
            assert hasattr(flex_rank, "league_points")

    def test_champion_stats_perfect_record(self):
        """Test ChampionStats with a perfect record (all wins, no deaths)."""
        from nexar import ChampionStats

        # Test perfect record (all wins, no deaths)
        perfect_stats = ChampionStats(
            champion_id=266,
            champion_name="Aatrox",
            games_played=3,
            wins=3,
            losses=0,
            total_kills=15,
            total_deaths=0,
            total_assists=20,
        )

        assert perfect_stats.win_rate == 100.0
        assert perfect_stats.avg_kills == 5.0
        assert perfect_stats.avg_deaths == 0.0
        assert perfect_stats.avg_assists == 20.0 / 3
        assert perfect_stats.avg_kda == 0.0  # Should return 0 when deaths is 0

    def test_champion_stats_realistic_values(self):
        """Test ChampionStats with realistic game values."""
        stats = ChampionStats(
            champion_id=157,
            champion_name="Yasuo",
            games_played=25,
            wins=12,
            losses=13,
            total_kills=187,
            total_deaths=203,
            total_assists=234,
        )

        assert stats.win_rate == 48.0  # 12/25 * 100
        assert stats.avg_kills == 7.48  # 187/25
        assert stats.avg_deaths == 8.12  # 203/25
        assert stats.avg_assists == 9.36  # 234/25
        assert abs(stats.avg_kda - ((187 + 234) / 203)) < 0.01  # ~2.07

    def test_champion_stats_data_integrity(self):
        """Test that ChampionStats maintains data integrity."""
        stats = ChampionStats(
            champion_id=1,
            champion_name="Annie",
            games_played=7,
            wins=3,
            losses=4,
            total_kills=21,
            total_deaths=28,
            total_assists=35,
        )

        # Games played should equal wins + losses
        assert stats.games_played == stats.wins + stats.losses

        # All totals should be non-negative
        assert stats.total_kills >= 0
        assert stats.total_deaths >= 0
        assert stats.total_assists >= 0
        assert stats.wins >= 0
        assert stats.losses >= 0
        assert stats.games_played >= 0

        # Win rate should be between 0 and 100
        assert 0.0 <= stats.win_rate <= 100.0
