# Nexar

Simple League of Legends SDK with rate limiting & disk caching by default.

Trying to restore the glory days, pre Riot IDs.

> [!Important]
> Unreleased, unversioned, subject to breaking changes and squashed git histories

## Why Nexar?

Python through and through. Dates? `datetime`. So many enums you'll hate it. Comparable, iterable objects. Type safe. Everything you'd hope for (I hope).

Totally wrapped lower API, and dead simple high level API allows you to pull League data like ranks, match history, champion history, with ease.

Forget Riot IDs. Just use `NexarClient.get_player("username", "tag")` and explore with your IDE. Tons of helpful doc strings and tips. 

## Quick Start

```python
import os
from datetime import datetime

from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5

# Create client
client = NexarClient(
    riot_api_key=os.getenv("RIOT_API_KEY"),
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
    cache_config=SMART_CACHE_CONFIG,
)

# Get player information
player = client.get_player("bexli", "bex")

print()
print(f"Summoner: {player.riot_account.game_name}")
print(f"Level: {player.summoner.summoner_level}")
if player.rank:
    rank_text = f"{player.rank.tier.value.title()} {player.rank.rank.value}"
    print(f"Solo Queue rank: {rank_text}\n")

# Get and display recent matches
recent_matches = player.get_recent_matches(count=5)
print(f"Recent Match History ({len(recent_matches)} matches):\n")

for match in recent_matches:
    # Find player's performance in this match
    for participant in match.info.participants:
        if participant.puuid == player.puuid:
            result = "Victory!" if participant.win else "Defeat."
            kda = participant.kda(as_str=True)
            kda_ratio = f"{participant.challenges.kda:.2f}"

            days_ago = (datetime.today() - match.info.game_start_timestamp).days
            days_ago_str = f"{days_ago:} {'day' if days_ago == 1 else 'days'} ago"

            print(
                f"{days_ago_str:<10} "
                f"{result:<9} "
                f"{participant.champion_name:<8} "
                f"{participant.team_position.value.title():<6} "
                f"{kda} ({kda_ratio})"
            )
            break

```

## Documentation

For detailed information, see the documentation:

- [Player API Guide](docs/player-api.md) - Comprehensive Player class documentation
- [Caching Guide](docs/caching.md) - Advanced caching configuration and performance
- [Examples](examples/) - Code examples for common use cases

## Development and contributing

### Contributing

Features requests should start as issues. Bugs may start as PRs.

```sh
# Fork the repo

# Clone fork locally
git clone https://github.com/username/nexar

# Make changes on branch

# Ensure functionality and new tests if needed

# Ensure tests are still passing

# Make PR
```

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

## LLMs and the project

Tests, examples, transforming the API response schemas to models, and other large scale chores were contributed by [Github Copilot](https://docs.github.com/en/copilot/how-tos/completions/getting-code-suggestions-in-your-ide-with-github-copilot) with [Anthropic's Claude Sonnet 4]([https://](https://www.anthropic.com/claude/sonnet)) model.

Cheers to the Anthropic team. This was the only model that didn't make me want to tear my hair out. Easily saved me hours of boring contributions.

### LLM Contributions

Used sparingly, and in the same fashion as above, it would hypocritical to not allow LLM contributions. But vibe coded, unchecked, slop may result in ban.
