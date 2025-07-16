# Why not Nexar?

At this time, Nexar is intended for personal projects, as the rate limiter is simple, and I'm unsure how it work at scale.

## Infancy

Project is very new and functionality is well suited for my usecases.

Issues are encouraged for features I haven't thought of.

## Simplicity

There's really nothing magic going on.

We're just using `aiohttp` to make async API calls, `aiolimiter` to stagger requests, then using the `aiohttp-client-cache` to save responses.

- Need the cache in a different format?
- Need some sort of middleware?
- Need a "production ready" solution?
- Need different rate limits for different endpoints?

Nexar is not for you.

## It's only League of Legends

Particularly League players and matches, of all game types.

No other Riot games will be supported, including "Teamfight Tactics".

Any TFT related issues or requests will be laughed at and closed.

## More SDK than wrapper

Nexar doesn't completely cover all League related endpoints, at least not yet. The goal of the project is stat pulling, particularly summoner and match history.

## Comparing Nexar to related libraries

|                           Library                            |      Async/sync      |   Wrapper only    |             Caching              |      Rate limiting      |   Active dev    |
| :----------------------------------------------------------: | :------------------: | :---------------: | :------------------------------: | :---------------------: | :-------------: |
|         [Nexar](https://github.com/joshpaulie/nexar)         | :green_circle: Async | :green_circle: No | :green_circle: SQLite, in-memory | :green_circle:  Simple  | :green_circle:  |
|      [Pulsefire](https://github.com/iann838/pulsefire)       | :green_circle: Async | :red_circle: Yes  |  :green_circle: Many solutions   | :green_circle:  Precise | :green_circle:  |
| [Cassiopeia](https://github.com/meraki-analytics/cassiopeia) |  :red_circle: Sync   | :green_circle: No |  :yellow_circle: In-memory[^1]   | :green_circle: Precise  | :yellow_circle: |
| [RiotWatcher](https://github.com/pseudonym117/Riot-Watcher)  |  :red_circle: Sync   | :red_circle: Yes  |        :red_circle: None         |  :yellow_circle: Naive  | :yellow_circle: |
|           [Pyot](https://github.com/iann838/Pyot)            | :green_circle: Async | :green_circle: No |  :green_circle: Many solutions   | :green_circle: Precise  |  :red_circle:   |

[^1]: An disk caching plugin package is available

**Pulsefire is the recommended Nexar alternative**. Async, type safe, idiomatic and completley wraps all Riot Games APIs.

Nexar was created as a simpler (and "League only") Pulsefire alternative, focusing on developer experience (helper functions, robust models, doc strings galore, and usage examples). It's heavily inspired by Pulsefire's predicate library, Pyot.

Nexar is no where near production ready, while Pulsefire is.
