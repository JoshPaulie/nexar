# Quick Start

## The client

The primary object for Nexar is the `NexarClient`.

Here you set your Riot API key, pick a cache type (if any), and optionally set default regions(1) for your lookups.
{ .annotate }

1. Helpful for personal projects, where you're only pulling stats for yourself and friends.

```py
-8<-- "quick_start/01_client_demo.py:declaration"
```

You can use the client in a couple of ways, but the most common will be:

```py
-8<-- "quick_start/01_client_demo.py:usage"
```

!!! Note

     All of the following examples will implicitly be done inside of this declared `async with client` context.

     **Snippets will also be de-indented for easier reading.**

## `Player`

The "heavylifter" model is `Player`. `Player` encapsulates multiple endpoints and allows you to elegantly make API calls and derive values without having to combine the output of many datapoints.

[Read the full `Player` docs here](reference/models/player.md)

### Getting players

To start, we either import Player and pass it our client, or use `NexarClient.get_player()`.

```py
-8<-- "quick_start/02_player.py:get-player"
```

You can even get multiple Players at a time(1):
{ .annotate }

1. Though, they must be of the same region.

```py
-8<-- "quick_start/02_player.py:get-players"
```

### Using `Player`

`Player` has quite a few convenience methods, like:

```py title="Current ranked standings"
-8<-- "quick_start/02_player.py:get-ranks"
```

```py title="Recent match history"
-8<-- "quick_start/02_player.py:get-matches"
```


```py title="Champion performance"
-8<-- "quick_start/02_player.py:champ-metrics"
        # Output: (1)
```

1.  
    ```
    Average KDA with Jinx: 2.91
    Average KDA with Jhin: 3.25
    Average KDA with Lillia: 2.09
    Average KDA with Warwick: 2.09
    Average KDA with Ashe: 2.50
    ```

## `Match`

Another powerful model is `Match`, particularly in combination with `Participant` & `ParticipantList`.

```py
-8<-- "quick_start/03_match.py:get-match"
```

### `Participant`

The difference between `Player` and `Participant` might be confusing.

A "participant" is 1 of 10 players (in a Summoner's Rift game, more or less for other modes). Attached to the `Participant` is all of the stats related to that player over the duration of the game.

```py
-8<-- "quick_start/03_match.py:participants"
# Output: (1)
```

1.  
    ```
    Winners! Mojo Jo 77, Bravo, GAMr Guy, bexli, MltSimpleton

    FugginSuggin (Darius) went 2/9/1
    HeckenGena (Belveth) went 3/7/4
    Cauris (Annie) went 2/12/8
    SupremeKing (Jinx) went 14/7/4
    Villain King (Karma) went 2/6/10
    Mojo Jo 77 (Mordekaiser) went 12/4/3
    Bravo (Amumu) went 9/3/6
    GAMr Guy (Xerath) went 5/6/11
    bexli (Jhin) went 11/6/8
    MltSimpleton (Senna) went 4/4/19
    ```

### `ParticipantList`

The easiest way to get a particular participant from a `Match` is using the very helpful `ParticipantList`, which is what is returned by `Match.participants`.

```py
-8<-- "quick_start/03_match.py:get-participant"
```

Afterwhich we can dig into the stats

```py
-8<-- "quick_start/03_match.py:participant"
```

You can also easily get a particular team from a Match.

```py
-8<-- "quick_start/03_match.py:get-team"
```
