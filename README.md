# Nexar

A simple League of Legends SDK with built-in rate limiting and disk caching.

Trying to restore the glory days, pre Riot IDs.

## Objective

Nexar is a Pythonic, League-only, async, opinionated, and simple SDK. It is not a wrapper. 

It's built for single-node, single-client projects and not intended for use at scale. If you need a distributed solution, look elsewhere. 

- Built for Python freaks.
- Robust models with datetime objects and enums.
- High-level API that abstracts the messy Riot API.
- Accurate in-memory rate limiting and disk caching.

Hate Riot IDs? Just `NexarClient.get_player("username", "tag", region=Region.NA1)` and explore with your IDE.

Packed with helpful doc strings and tips.

Check out [Why not Nexar?](docs/why-not-nexar.md) for more details.

## Installation

>[!tip]
> Considering I will likely be the only user of this library for the time being, Nexar is not published on PyPI. Install with `uv` or `pip` directly from the GitHub repo.
>
> If you are using or considering using Nexar, please reach out or star the repo. This would indicate to me an interest from the community, and I'd be happy to publish to PyPI and maintain a proper release cycle.

```bash
uv add "git+https://github.com/joshpaulie/nexar"
```

## Usage example

Below is a real, working example from `README_example.py`:

<!-- example-block-start -->
<!-- Use `uv run scripts/update_readme_example.py` to update this example -->
```python
"""Example from README showing async player information retrieval."""

import asyncio
import contextlib
import os
import sys
from datetime import UTC, datetime

from nexar.cache import DEFAULT_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import Region


async def main() -> None:
    """Demonstrate player information retrieval using the async API."""
    # Get API key from environment
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        sys.exit("Please set RIOT_API_KEY environment variable")

    # Create async client
    # Note: Using SQLite cache (default) persists API responses to disk while rate limits stay in-memory
    client = NexarClient(
        riot_api_key=api_key,
        default_region=Region.NA1,
        cache_config=DEFAULT_CACHE_CONFIG,
    )

    async with client:
        print("Fetching player info...")
        # Get player information
        player = await client.get_player("bexli", "bex")

        print()
        riot_account = player.riot_account  # Immediately available!
        summoner = await player.get_summoner()
        rank = await player.get_solo_rank()

        print(f"Summoner: {riot_account.game_name}#{riot_account.tag_line}")
        print(f"Level: {summoner.summoner_level}")

        if rank:
            print(f"Solo Queue rank: {rank.tier} {rank.division}\n")

        print("Fetching recent matches...")
        # Get and display recent matches
        recent_matches = await player.get_matches(count=5)
        print(f"Recent Match History ({len(recent_matches)} matches):\n")

        for match in recent_matches:
            # Get participant stats of particular summoner
            participant = match.participants.by_puuid(player.puuid)

            if not participant:
                continue

            result = "Victory!" if participant.win else "Defeat."
            kda = participant.kda(as_str=True)
            kda_ratio = "N/A"
            if participant.challenges:
                kda_ratio = f"{participant.challenges.kda:.2f}"

            # Calculate time ago
            game_start = match.info.game_start_timestamp
            # Ensure game_start is timezone-aware
            if game_start.tzinfo is None:
                game_start = game_start.replace(tzinfo=UTC)

            days_ago = (datetime.now(tz=UTC) - game_start).days

            if days_ago == 0:
                time_str = "Today"
            elif days_ago == 1:
                time_str = "Yesterday"
            else:
                time_str = f"{days_ago} days ago"

            print(
                f"{time_str:<12} "
                f"{result:<9} "
                f"{participant.champion_name:<10} "
                f"{participant.team_position.value.title():<8} "
                f"{kda} ({kda_ratio})",
            )


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
```
<!-- example-block-end -->

### Example Output

<!-- example-output-block-start -->
```
Summoner: bexli#bex
Level: 543
Solo Queue rank: Gold IV

Fetching recent matches...
Recent Match History (5 matches):

3 days ago   Victory!  Lillia     Jungle   6/5/10 (3.20)
3 days ago   Defeat.   Jinx       Bottom   15/9/5 (2.22)
4 days ago   Victory!  Jhin       Bottom   4/5/5 (1.80)
4 days ago   Victory!  Jhin       Bottom   0/0/0 (0.00)
10 days ago  Defeat.   Jhin       Bottom   5/8/7 (1.50)
```
<!-- example-output-block-end -->

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

Tests, transforming the API response schemas to models, and other large scale chores were contributed by an assortment of LLMs. The client, cache, rate limiter, and accompanying logic were written by hand, and likely much worse for it. Rest easy knowing this was mostly created by a fallible human, as `$DEITY` intended.

For some reading on how AI almost ruined this project, check out the [llm post-mortem](docs/llm-post-mortem.md).

### LLM Contributions

Used sparingly, and in the same fashion as above, it would hypocritical to not allow LLM contributions. But vibe coded, unchecked, slop may result in ban.
