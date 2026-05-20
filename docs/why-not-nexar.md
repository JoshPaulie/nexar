# Why not Nexar?

Nexar is intended for personal or small scale (single node) use. Distributed caching and rate limiting are not supported, and likely never will be.

## Infancy

Project is very new and functionality is well suited for my usecases.

Issues are encouraged for features I haven't thought of.

## Simplicity

There's really nothing magic going on.

It's just `aiohttp` to make async API calls with an `aiolimiter` leaky bucket rate limiter, then use `aiohttp-client-cache` to save responses to disk.

- Need the cache in a different format?
- Need some sort of middleware?
- Need a "production ready" rate limiter (or production-anything)?
- Need different rate limits for different endpoints?

Nexar is not for you. Read [more below](#the-recommended-alternative).

## It's only League of Legends

Particularly League players and matches, of all game types.

No other Riot games will be supported, especially Teamfight Tactics.

Any TFT related issues or requests will be laughed at and closed.

## More SDK than wrapper

I wanted Nexar to be a bit more of a complete package, documenting and stitching together the oddities of the Riot API, rather than just a thin wrapper around it.

In other words, this is intended for hobbyists; people who just want to get an API key and start pulling stats with terminology that makes sense to them, not learning the Riot API from scratch.

## The recommended alternative

[Pulsefire](https://github.com/iann838/pulsefire) is the recommended Nexar alternative. Async, type safe, idiomatic and completely wraps all Riot Games APIs.

Nexar was created as a simple, League-only Pulsefire alternative, focusing on developer experience (helper functions, robust models, doc strings galore, and usage examples). It's heavily inspired by Pulsefire's predicate library, Pyot.
