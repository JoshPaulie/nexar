# Why not Nexar?

Nexar is intended for personal or small scale (single node) use. Distributed caching and rate limiting are not supported, and likely never will be.

## Infancy

Project is very new and functionality is well suited for my usecases.

Issues are encouraged for features I haven't thought of.

## Simplicity

There's really nothing magic going on.

It's just `aiohttp` to make async API calls with a custom in-memory rate limiter, then use `aiohttp-client-cache` to save responses to disk.

- Need the cache in a different format?
- Need some sort of middleware?
- Need a "production ready" solution?
- Need different rate limits for different endpoints?

Nexar is not for you.

## It's only League of Legends

Particularly League players and matches, of all game types.

No other Riot games will be supported, especially Teamfight Tactics.

Any TFT related issues or requests will be laughed at and closed.

## More SDK than wrapper

Nexar doesn't completely cover all League related endpoints, at least not yet. The goal is stat pulling, particularly summoner and match history.

## Comparing Nexar to related libraries

|                           Library                            | Async/sync | Wrapper only |       Caching       | Rate limiting | Active dev |
| :----------------------------------------------------------: | :--------: | :----------: | :-----------------: | :-----------: | :--------: |
|         [Nexar](https://github.com/joshpaulie/nexar)         |   Async    |      No      | SQLite or in-memory |    Precise    |    Yes     |
|      [Pulsefire](https://github.com/iann838/pulsefire)       |   Async    |     Yes      |   Many solutions    |    Precise    |    Yes     |
| [Cassiopeia](https://github.com/meraki-analytics/cassiopeia) |    Sync    |      No      |    In-memory[^1]    |    Precise    |  Partial   |
| [RiotWatcher](https://github.com/pseudonym117/Riot-Watcher)  |    Sync    |     Yes      |        None         |     Naive     |  Partial   |
|           [Pyot](https://github.com/iann838/pyot)            |   Async    |      No      |   Many solutions    |    Precise    |     No     |

[^1]: A disk caching plugin package is available

Pulsefire is the recommended Nexar alternative. Async, type safe, idiomatic and completely wraps all Riot Games APIs.

Nexar was created as a simpler, League-only Pulsefire alternative, focusing on developer experience (helper functions, robust models, doc strings galore, and usage examples). It's heavily inspired by Pulsefire's predicate library, Pyot.

Nexar is nowhere near "production ready" in the enterprise sense, but it's perfect for your personal projects.
