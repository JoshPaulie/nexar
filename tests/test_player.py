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

    def test_player_get_last_20(self, client):
        """Test getting last 20 matches."""
        player = client.get_player("bexli", "bex")

        matches = player.get_last_20()
        assert isinstance(matches, list)
        assert len(matches) <= 20

    def test_player_get_last_20_with_queue_filter(self, client):
        """Test getting last 20 matches with queue filter."""
        player = client.get_player("bexli", "bex")

        matches = player.get_last_20(queue=QueueId.RANKED_SOLO_5x5)
        assert isinstance(matches, list)
        assert len(matches) <= 20

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


class TestChampionStats:
    """Test the ChampionStats class."""

    def test_champion_stats_properties(self):
        """Test ChampionStats calculated properties."""
        stats = ChampionStats(
            champion_id=1,
            champion_name="Annie",
            games_played=10,
            wins=6,
            losses=4,
            total_kills=50,
            total_deaths=30,
            total_assists=80,
        )

        assert stats.win_rate == 60.0
        assert stats.avg_kills == 5.0
        assert stats.avg_deaths == 3.0
        assert stats.avg_assists == 8.0
        assert stats.avg_kda == (50 + 80) / 30  # (kills + assists) / deaths

    def test_champion_stats_edge_cases(self):
        """Test ChampionStats with edge case values."""
        # No games played
        stats = ChampionStats(
            champion_id=1,
            champion_name="Annie",
            games_played=0,
            wins=0,
            losses=0,
            total_kills=0,
            total_deaths=0,
            total_assists=0,
        )

        assert stats.win_rate == 0.0
        assert stats.avg_kills == 0.0
        assert stats.avg_deaths == 0.0
        assert stats.avg_assists == 0.0
        assert stats.avg_kda == 0.0

        # No deaths (perfect KDA)
        stats = ChampionStats(
            champion_id=1,
            champion_name="Annie",
            games_played=5,
            wins=5,
            losses=0,
            total_kills=25,
            total_deaths=0,
            total_assists=40,
        )

        assert stats.win_rate == 100.0
        assert stats.avg_kills == 5.0
        assert stats.avg_deaths == 0.0
        assert stats.avg_assists == 8.0
        assert stats.avg_kda == 0.0  # Should return 0 when deaths is 0
