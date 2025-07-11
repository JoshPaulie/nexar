# Nexar

A simple League of Legends SDK with built-in rate limiting & disk caching.

Trying to restore the glory days, pre Riot IDs.

> [!Warning]
> This is an active hacking zone. Breaking changes, unversioned, pushing to main.
>
> The goal is create a solid MVP, then squash git history. Do not clone at this point. :smile:

## Why Nexar?

- Built for Python freaks.
    - Robust, Pythonic models
    - Timestamps are `datetime` objects
    - So many enums you'll hate them (but autocomplete makes it worth)
- Clean high-level API wraps the messy Riot API underneath.
- Pull player ranks, match history, and champion stats with just a few lines of code.

Hate Riot IDs? Who doesn't. Just `NexarClient.get_player("username", "tag")` and explore with your IDE.

Packed with helpful doc strings and tips.

> Check out [Why not Nexar?](docs/why-not-nexar.md) for more

## Usage example

Below is a real, working example from `examples/basic/README_example.py`:

<!-- example-block-start -->
```python
"""Example from README showing async player information retrieval."""

import asyncio
import os
import sys
from datetime import UTC, datetime

from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5


async def main() -> None:
    """Demonstrate player information retrieval using the async API."""
    # Get API key from environment
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        sys.exit("Please set RIOT_API_KEY environment variable")

    # Create async client
    client = NexarClient(
        riot_api_key=api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
        cache_config=SMART_CACHE_CONFIG,
    )

    async with client:
        # Get player information
        player = await client.get_player("bexli", "bex")

        print()
        riot_account = player.riot_account  # Immediately available!
        summoner = await player.get_summoner()
        rank = await player.get_solo_rank()

        print(f"Summoner: {riot_account.game_name}")
        print(f"Level: {summoner.summoner_level}")

        if rank:
            print(f"Solo Queue rank: {rank.tier} {rank.division}\n")

        # Get and display recent matches
        recent_matches = await player.get_matches(count=5)
        print(f"Recent Match History ({len(recent_matches)} matches):\n")

        for match in recent_matches:
            # Get participant stats of particular summoner
            participant = match.participants.by_puuid(player.puuid)

            result = "Victory!" if participant.win else "Defeat."
            kda = participant.kda(as_str=True)
            kda_ratio = f"{participant.challenges.kda:.2f}"

            days_ago = (datetime.now(tz=UTC) - match.info.game_start_timestamp.replace(tzinfo=UTC)).days
            days_ago_str = f"{days_ago} {'day' if days_ago == 1 else 'days'} ago"

            print(
                f"{days_ago_str:<10} "
                f"{result:<9} "
                f"{participant.champion_name:<8} "
                f"{participant.team_position.value.title():<6} "
                f"{kda} ({kda_ratio})",
            )


if __name__ == "__main__":
    asyncio.run(main())
```
<!-- example-block-end -->

### Example Output

<!-- example-output-block-start -->
```
Summoner: bexli
Level: 511
Solo Queue rank: Silver IV

Recent Match History (5 matches):

3 days ago Victory!  Jinx     Bottom 11/7/13 (3.43)
3 days ago Victory!  Jhin     Bottom 2/0/0 (2.00)
3 days ago Victory!  Jinx     Bottom 7/4/9 (4.00)
3 days ago Defeat.   Jinx     Bottom 4/5/4 (1.60)
3 days ago Defeat.   Warwick  Jungle 11/7/5 (2.29)
```
<!-- example-output-block-end -->

## Development and contributing

> [!Warning]
> Git history is subject to be broken at any point while project is unversioned.
>
> This is disclaimer will be removed once ready for contributions.

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

Tests, transforming the API response schemas to models, and other large scale chores were contributed by [Github Copilot](https://docs.github.com/en/copilot/how-tos/completions/getting-code-suggestions-in-your-ide-with-github-copilot) with [Anthropic's Claude Sonnet 4](https://www.anthropic.com/claude/sonnet) model.

Cheers to the Anthropic team. This was the only model that didn't make me want to tear my hair out. Easily saved me hours of boring contributions.

### LLM Contributions

Used sparingly, and in the same fashion as above, it would hypocritical to not allow LLM contributions. But vibe coded, unchecked, slop may result in ban.
