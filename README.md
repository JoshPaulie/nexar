# Nexar

Easy and simple Riot API SDK, for League of Legends only.

## Quick Start

```python
import logging
import os

import nexar
from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5

# Create client with "smart cache"
client = NexarClient(
    riot_api_key=os.getenv("RIOT_API_KEY"),
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
    cache_config=SMART_CACHE_CONFIG,
)

# Enable logging to see API calls and cache performance
nexar.configure_logging(logging.INFO)

# Get player information
player = client.get_player("bexli", "bex")
print(f"Summoner Level: {player.summoner.summoner_level}")
print(f"Rank: {player.rank.tier.value} {player.rank.rank.value}" if player.rank else "Unranked")

# Get recent matches
recent_matches = player.get_last_20()
print(f"Retrieved {len(recent_matches)} recent matches")

# Show recent match results
for i, match in enumerate(recent_matches[:3]):
    # Find this player's participant data
    player_participant = None
    for participant in match.info.participants:
        if participant.puuid == player.puuid:
            player_participant = participant
            break
    
    if player_participant:
        result = "Win" if player_participant.win else "Loss"
        kda = f"{player_participant.kills}/{player_participant.deaths}/{player_participant.assists}"
        print(f"Match {i+1}: {player_participant.champion_name} - {result} ({kda})")
```

## Features

### High-Level Player API
- Simple player object with automatic data aggregation
- Match history with filtering and analysis
- Champion statistics and performance metrics
- Rank information (Solo/Duo and Flex)

### Built-in Caching
- Automatic caching to reduce API calls and improve performance
- Smart per-endpoint TTL configuration
- 80-200x faster response times on cache hits

```python
from nexar import SMART_CACHE_CONFIG

# Enable intelligent caching (recommended)
client = NexarClient(
    riot_api_key="your_api_key",
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
    cache_config=SMART_CACHE_CONFIG,
)
```

### Type Safety
- Fully typed with Python type hints
- Enums for queues, regions, ranks, and more
- IDE autocompletion and error detection

## Documentation

For detailed information, see the documentation:

- [Player API Guide](docs/player-api.md) - Comprehensive Player class documentation
- [Caching Guide](docs/caching.md) - Advanced caching configuration and performance
- [Examples](examples/) - Code examples for common use cases

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
