# Why not Nexar?

It's written by an idiot, very simple.

## Synchronous

The goal a quick solution for my other project, which ironically is asynchronous. I wanted to hack to together a working solution, so maybe an async version (or full rewrite) in future.

> The only asynchronous alternative I can recommend is [Pulsefire](https://pulsefire.iann838.com). It's superb. Note that it's pretty advanced, and strictly a wrapper.

## It's only League of Legends

Particularly League players and matches, of all game types.

No other Riot games will be supported, including "Teamfight Tactics".

Any TFT related issues or requests will be laughed at and closed.

## Kinda high level

The goal is encapsulate and abstract away the Riot API. Some lower level functionality is still there and wrapped, but I presume almost all Nexar integration will start and end with `NexarClient.get_player()`.
