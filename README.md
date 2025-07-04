# Nexar

League of Legends SDK. Pythonic wrapper for Riot's LoL API.

## Quick Start

```python
from nexar import NexarClient, RegionV4, RegionV5

# Create client
client = NexarClient(
    riot_api_key="your_api_key",
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
)

# Create a player object (abstracts riot id lookup)
player = client.get_player("game_name", "tag_line")

# Access player information
print(f"Summoner Level: {player.summoner.summoner_level}")
print(f"Rank: {player.rank.tier.value} {player.rank.rank.value}" if player.rank else "Unranked")

# Get recent matches
recent_matches = player.get_last_20()

# Get champion statistics
top_champions = player.get_top_champions(top_n=5)
for champ in top_champions:
    print(f"{champ.champion_name}: {champ.games_played} games, {champ.win_rate:.1f}% WR")

# Get performance summary
stats = player.get_performance_summary(count=20)
print(f"Recent performance: {stats['win_rate']}% WR over {stats['total_games']} games")
```

## Player API Features

The `Player` class provides high-level access to player data:

### Basic Information
- `player.summoner` - Summoner details (level, etc.)
- `player.puuid` - Player's PUUID
- `player.rank` - Solo queue rank
- `player.flex_rank` - Flex queue rank

### Match History
- `player.get_last_20()` - Get last 20 matches
- `player.get_recent_matches(count=50, queue=QueueId.RANKED_SOLO_5x5)` - Flexible match filtering

### Champion Statistics
- `player.get_top_champions(top_n=5)` - Most played champions
- `player.get_champion_stats()` - Detailed per-champion statistics

### Performance Analysis
- `player.get_performance_summary()` - Overall performance metrics
- `player.is_on_win_streak()` - Check for win streaks
- `player.get_recent_performance_by_role()` - Performance by position

### Caching
Player objects cache expensive API calls automatically:
- `player.refresh_cache()` - Clear cache to force fresh data

## Development

### Running Tests

Tests use real Riot API calls rather than mocks. You'll need a valid Riot API key:

1. Copy `riot-key.sh.example` to `riot-key.sh`
2. Add your Riot API key to `riot-key.sh`
3. Run tests with the provided script:

```bash
./run_tests.sh
```

The script automatically sources your API key and runs the test suite.

### Test Requirements

- Valid Riot API key
- Active internet connection
- Tests may be rate-limited by Riot's API
