# Player API

The `Player` class provides high-level access to player data with automatic caching and data aggregation. Player objects now use **eager loading** for Riot account data, meaning the account information is fetched immediately when the player is created.

## Basic Usage

```python
import asyncio
import os
import sys

from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5
from nexar.cache import SMART_CACHE_CONFIG

async def main() -> None:
    # Get API key from environment
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        sys.exit("Please set RIOT_API_KEY environment variable")

    # Create async client
    async with NexarClient(
        riot_api_key=api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
        cache_config=SMART_CACHE_CONFIG,
    ) as client:
        # Create a player object (riot account fetched immediately)
        player = await client.get_player("bexli", "bex")
        
        # Access player data (riot account already available)
        riot_account = player.riot_account  # No await needed!
        summoner = await player.get_summoner()
        print(f"Player: {riot_account.game_name}#{riot_account.tag_line}")
        print(f"Level: {summoner.summoner_level}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Alternative Player Creation

You can also create players directly using the factory methods:

```python
# Using Player.create()
player = await Player.create(
    client=client,
    game_name="bexli", 
    tag_line="bex"
)

# Using Player.by_riot_id()
player = await Player.by_riot_id(
    client=client,
    riot_id="bexli#bex"
)
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
- `player.puuid` - Player's PUUID (immediately available)
- `player.game_name` - Riot ID game name (immediately available)
- `player.tag_line` - Riot ID tag line (immediately available)
- `player.riot_account` - Complete riot account data (immediately available)

### Summoner Data
- `player.summoner` - Summoner details (level, etc.)
- `player.summoner.summoner_level` - Current summoner level
- `player.summoner.profile_icon_id` - Profile icon ID

### Ranking Information
- `await player.get_solo_rank()` - Solo queue rank
- `await player.get_flex_rank()` - Flex queue rank

```python
# Check rank information
rank = await player.get_solo_rank()
if rank:
    print(f"Solo Queue: {rank.tier.value} {rank.rank.value}")
    print(f"LP: {rank.league_points}")
    print(f"Win Rate: {rank.wins}/{rank.wins + rank.losses}")

flex_rank = await player.get_flex_rank()
if flex_rank:
    print(f"Flex Queue: {flex_rank.tier.value} {flex_rank.rank.value}")
```

## Match History

### Basic Match Retrieval
```python
# Get recent matches (replaces the non-existent get_last_20 method)
recent_matches = await player.get_matches(count=20)

# Get custom number of matches  
matches = await player.get_matches(count=50)

# Filter by queue type
ranked_matches = await player.get_matches(
    count=30, 
    queue=QueueId.RANKED_SOLO_5x5
)
```

### Match Analysis
```python
for match in recent_matches:
    # Find the participant for this player
    participant = None
    for p in match.info.participants:
        if p.puuid == player.puuid:
            participant = p
            break
    
    if participant:
        print(f"Champion: {participant.champion_name}")
        print(f"KDA: {participant.kills}/{participant.deaths}/{participant.assists}")
        print(f"Result: {'Win' if participant.win else 'Loss'}")
```

## Champion Statistics

### Top Champions
```python
# Get most played champions
top_champions = await player.get_top_champions(top_n=5)

for champ in top_champions:
    print(f"{champ.champion_name}:")
    print(f"  Games: {champ.games_played}")
    print(f"  Win Rate: {champ.win_rate:.1f}%")
    print(f"  Avg KDA: {champ.avg_kills:.1f}/{champ.avg_deaths:.1f}/{champ.avg_assists:.1f}")
```

### Detailed Champion Stats
```python
# Get all champion statistics
all_champion_stats = await player.get_champion_stats()

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
stats = await player.get_performance_summary(count=20)

print(f"Win Rate: {stats['win_rate']:.1f}%")
print(f"Total Games: {stats['total_games']}")
print(f"Average KDA: {stats['avg_kda']:.2f}")
print(f"Average CS: {stats['avg_cs']:.1f}")
print(f"Average Game Duration: {stats['avg_game_duration_minutes']:.1f}m")
```

### Win Streaks
```python
# Check for win streaks
if await player.is_on_win_streak():
    print("Player is on a win streak!")
    
# Get recent performance by role
role_performance = await player.get_recent_performance_by_role()
for role, stats in role_performance.items():
    print(f"{role}: {stats['games']} games, {stats['win_rate']:.1f}% WR")
```

## Advanced Usage

### Custom Match Filtering
```python
import asyncio
from datetime import datetime, timedelta
from nexar.enums import QueueId

# Get matches from the last week
one_week_ago = datetime.now() - timedelta(days=7)
recent_week = await player.get_matches(
    count=100,
    start_time=one_week_ago,
    queue=QueueId.RANKED_SOLO_5x5
)
```

### Performance Trends
```python
# Analyze performance over time
matches = await player.get_matches(count=50)
recent_10 = matches[:10]
older_10 = matches[40:50]

# Calculate win rates for recent vs older matches
recent_wr = 0
older_wr = 0
puuid = player.riot_account.puuid  # Direct access, no await needed

for m in recent_10:
    for p in m.info.participants:
        if p.puuid == puuid and p.win:
            recent_wr += 1
            break
recent_wr = recent_wr / len(recent_10) if recent_10 else 0

for m in older_10:
    for p in m.info.participants:
        if p.puuid == puuid and p.win:
            older_wr += 1
            break
older_wr = older_wr / len(older_10) if older_10 else 0

print(f"Recent 10 games: {recent_wr:.1%} WR")
print(f"Games 40-50: {older_wr:.1%} WR")
print(f"Trend: {'Improving' if recent_wr > older_wr else 'Declining'}")
```

## Caching

Player objects automatically benefit from caching when the underlying `NexarClient` has caching enabled:

```python
from nexar.cache import SMART_CACHE_CONFIG

# Client with caching
client = NexarClient(
    riot_api_key="your_api_key",
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
    cache_config=SMART_CACHE_CONFIG,
)

# All player operations will use caching
player = await client.get_player("bexli", "bex")  # May be cached
recent_matches = await player.get_matches(count=20)  # May be cached
```

### Manual Cache Management
```python
# Force refresh of cached data
player.refresh_cache()

# Check if data is likely cached
info = await client.get_cache_info()
print(f"Cache enabled: {info['enabled']}")
```

## Error Handling

```python
from nexar.exceptions import NotFoundError, RateLimitError

try:
    player = await client.get_player("nonexistent", "player")
    matches = await player.get_matches(count=20)
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
6. **Take advantage of eager loading** - riot account data is immediately available without additional API calls

## Key Benefits of Eager Loading

- **Immediate Access**: `player.riot_account` is available instantly without await
- **Better Performance**: No repeated API calls for riot account data
- **Cleaner Code**: No need to manage riot account fetching state
- **Consistent Behavior**: All players always have complete identity information
