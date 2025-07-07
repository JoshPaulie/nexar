# Why not Nexar?

## Infancy

Project is very new and functionality is well suited for _my_ usecases.

> Issues are encouraged for features I haven't thought of.

## Simplicity

There's really nothing magic going on.

We're just using aiohttp to make async API calls, then using the related aiohttp caching library to save responses.

Need the cache in a different format? Need some sort of middleware? Nexar is not for you.

## It's only League of Legends

Particularly League players and matches, of all game types.

No other Riot games will be supported, including "Teamfight Tactics".

Any TFT related issues or requests will be laughed at and closed.

## More SDK than wrapper

If you need a phenomenal, async, type safe, & idiomatic wrapper, I can't recommend [Pulsefire](https://pulsefire.iann838.com) enough.

Pulsefire provides wrappers for every Riot API call (for all games), and returns a TypedDict response. It's nothing short of magic.

Nexar was created as a simpler, League focused alternative, focusing on developer experience (helper functions, robust models, doc strings galore, and usage examples).
