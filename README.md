# Nexar

A simple, League-only Python SDK for the Riot API: typed models, built-in rate limiting, and disk caching.

## Objective

Nexar is more SDK than wrapper: a Pythonic, async, opinionated, League-only SDK that stitches together the oddities of the Riot API (region vs platform routing, epoch timestamps, silently omitted fields), so you can get an API key and start pulling stats in terminology that makes sense to you, instead of learning the Riot API from scratch.

It's built for single-node, single-client projects and not intended for use at scale. If you need a distributed solution, look elsewhere. 

- Built for Python freaks.
- Robust models with datetime objects and enums.
- High-level API that abstracts the messy Riot API.
- In-memory sliding-window rate limiting.
- Rate limiting auto-aligns with the server: fresh clients seed their windows from Riot's reported usage counts, and 429s back off for `Retry-After`.
- API responses cached to disk, SQLite by default.
- Packed with helpful doc strings and tips.

Check out [Why not Nexar?](https://bexli.dev/nexar/why-not-nexar/) for scope, expectations, and the recommended alternative.

## Installation

>[!tip]
> Nexar isn't on PyPI. Install from GitHub with `uv` or `pip`, and star the repo or reach out if you use it. If there's enough interest from the community, I'll happily publish to PyPI and maintain a proper release cycle.

Requires **Python 3.13 or newer** (`requires-python = ">=3.13"` in `pyproject.toml`).

```bash
uv add "git+https://github.com/joshpaulie/nexar"
```

## Usage example

Below is a real, working example from `README_example.py`:

<!-- example-block-start -->
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
        player = await client.get_player(game_name="bexli", tag_line="bex")

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
            kda_ratio = f"{participant.kda():.2f}"

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
Level: 549
Solo Queue rank: Gold IV

Fetching recent matches...
Recent Match History (5 matches):

10 days ago  Defeat.   Jinx       Bottom   15/8/6 (2.62)
10 days ago  Defeat.   Draven     Bottom   6/12/5 (0.92)
10 days ago  Defeat.   Warwick    Jungle   15/8/9 (3.00)
10 days ago  Victory!  Warwick    Jungle   11/2/8 (9.50)
10 days ago  Defeat.   Shaco      Jungle   2/5/5 (1.40)
```
<!-- example-output-block-end -->

## Docs

Read the docs at [bexli.dev/nexar](https://bexli.dev/nexar): quick start, worked examples, the API surface (every wrapped op with its method and return model), and the full reference. The raw markdown under `docs/` doesn't render its snippet includes on GitHub, so read it from the site.

Development and contributing moved to [CONTRIBUTORS.md](CONTRIBUTORS.md).

---

Required legal disclaimer:

*Nexar is not endorsed by Riot Games and does not reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games and all associated properties are trademarks or registered trademarks of Riot Games, Inc.*
