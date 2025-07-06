# Player API

The `Player` class provides high-level access to player data with automatic caching and data aggregation.

## Basic Usage

```python
from nexar import NexarClient, RegionV4, RegionV5

client = NexarClient(
    riot_api_key="your_api_key",
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
)

# Create a player object
player = client.get_player("game_name", "tag_line")
```

## Batch Player Retrieval

For efficient retrieval of multiple players, use the `get_players()` method which fetches players in parallel:

```python
async with client:
    # Get multiple players efficiently using parallel processing
    riot_ids = ["mltsimpleton#na1", "roninalex#na1", "bexli#bex"]
    players = await client.get_players(riot_ids)
    
    # All players are pre-validated and ready to use
    for player in players:
        summoner = await player.get_summoner()
        print(f"{player}: Level {summoner.summoner_level}")
```

### Benefits of Batch Retrieval
- **Parallel Processing**: Uses `asyncio.gather()` for concurrent API calls
- **Pre-validation**: Ensures all players exist before returning
- **Efficient**: Reduces total request time compared to sequential calls
- **Error Handling**: Fails fast if any player doesn't exist

### Usage Tips
```python
# Handle invalid formats
try:
    players = await client.get_players(["ValidName#TAG", "invalid_format"])
except ValueError as e:
    print(f"Invalid Riot ID format: {e}")

# Empty list handling
empty_players = await client.get_players([])  # Returns []

# Single player (still uses async pattern)
single_player = await client.get_players(["Player#TAG"])  # Returns [Player]
```

## Basic Information

### Player Identity
- `player.puuid` - Player's PUUID
- `player.game_name` - Riot ID game name
- `player.tag_line` - Riot ID tag line

### Summoner Data
- `player.summoner` - Summoner details (level, etc.)
- `player.summoner.summoner_level` - Current summoner level
- `player.summoner.profile_icon_id` - Profile icon ID

### Ranking Information
- `player.rank` - Solo queue rank
- `player.flex_rank` - Flex queue rank

```python
# Check rank information
if player.rank:
    print(f"Solo Queue: {player.rank.tier.value} {player.rank.rank.value}")
    print(f"LP: {player.rank.league_points}")
    print(f"Win Rate: {player.rank.wins}/{player.rank.wins + player.rank.losses}")

if player.flex_rank:
    print(f"Flex Queue: {player.flex_rank.tier.value} {player.flex_rank.rank.value}")
```

## Match History

### Basic Match Retrieval
```python
# Get last 20 matches
recent_matches = player.get_last_20()

# Get custom number of matches
matches = player.get_recent_matches(count=50)

# Filter by queue type
ranked_matches = player.get_recent_matches(
    count=30, 
    queue=QueueId.RANKED_SOLO_5x5
)
```

### Match Analysis
```python
for match in recent_matches:
    participant = match.get_participant_by_puuid(player.puuid)
    print(f"Champion: {participant.champion_name}")
    print(f"KDA: {participant.kills}/{participant.deaths}/{participant.assists}")
    print(f"Result: {'Win' if participant.win else 'Loss'}")
```

## Champion Statistics

### Top Champions
```python
# Get most played champions
top_champions = player.get_top_champions(top_n=5)

for champ in top_champions:
    print(f"{champ.champion_name}:")
    print(f"  Games: {champ.games_played}")
    print(f"  Win Rate: {champ.win_rate:.1f}%")
    print(f"  Avg KDA: {champ.avg_kills:.1f}/{champ.avg_deaths:.1f}/{champ.avg_assists:.1f}")
```

### Detailed Champion Stats
```python
# Get all champion statistics
all_champion_stats = player.get_champion_stats()

# Filter for specific champion
yasuo_stats = [
    stats for stats in all_champion_stats 
    if stats.champion_name == "Yasuo"
]
```

## Performance Analysis

### Overall Performance
```python
# Get performance summary
stats = player.get_performance_summary(count=20)

print(f"Win Rate: {stats['win_rate']:.1f}%")
print(f"Total Games: {stats['total_games']}")
print(f"Average KDA: {stats['avg_kda']:.2f}")
print(f"Average CS/min: {stats['avg_cs_per_min']:.1f}")
```

### Win Streaks
```python
# Check for win streaks
if player.is_on_win_streak():
    print("Player is on a win streak!")
    
# Get recent performance by role
role_performance = player.get_recent_performance_by_role()
for role, stats in role_performance.items():
    print(f"{role}: {stats['games']} games, {stats['win_rate']:.1f}% WR")
```

## Advanced Usage

### Custom Match Filtering
```python
from datetime import datetime, timedelta
from nexar import QueueId

# Get matches from the last week
one_week_ago = datetime.now() - timedelta(days=7)
recent_week = player.get_recent_matches(
    count=100,
    start_time=one_week_ago,
    queue=QueueId.RANKED_SOLO_5x5
)
```

### Performance Trends
```python
# Analyze performance over time
matches = player.get_recent_matches(count=50)
recent_10 = matches[:10]
older_10 = matches[40:50]

recent_wr = sum(1 for m in recent_10 if m.get_participant_by_puuid(player.puuid).win) / len(recent_10)
older_wr = sum(1 for m in older_10 if m.get_participant_by_puuid(player.puuid).win) / len(older_10)

print(f"Recent 10 games: {recent_wr:.1%} WR")
print(f"Games 40-50: {older_wr:.1%} WR")
print(f"Trend: {'Improving' if recent_wr > older_wr else 'Declining'}")
```

## Caching

Player objects automatically benefit from caching when the underlying `NexarClient` has caching enabled:

```python
from nexar import SMART_CACHE_CONFIG

# Client with caching
client = NexarClient(
    riot_api_key="your_api_key",
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
    cache_config=SMART_CACHE_CONFIG,
)

# All player operations will use caching
player = client.get_player("bexli", "bex")  # May be cached
recent_matches = player.get_last_20()        # May be cached
```

### Manual Cache Management
```python
# Force refresh of cached data
player.refresh_cache()

# Check if data is likely cached
info = player.client.get_cache_info()
print(f"Cache enabled: {info['enabled']}")
```

## Error Handling

```python
from nexar.exceptions import NotFoundError, RateLimitError

try:
    player = client.get_player("nonexistent", "player")
    matches = player.get_last_20()
except NotFoundError:
    print("Player not found")
except RateLimitError:
    print("Rate limited, try again later")
```

## Best Practices

1. **Use caching** for better performance and to avoid rate limits
2. **Batch operations** when possible to reduce API calls
3. **Handle errors gracefully** for better user experience
4. **Cache player objects** in your application to avoid repeated lookups
5. **Use appropriate match counts** - don't request more data than you need
