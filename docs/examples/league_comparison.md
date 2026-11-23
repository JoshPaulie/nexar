# League Comparison

[`LeagueEntry`][nexar.models.league.LeagueEntry] supports rich comparison operators (`<`, `>`, [`is_higher_rank_than`][nexar.models.league.LeagueEntry.is_higher_rank_than]) and provides a [`rank_tuple`][nexar.models.league.LeagueEntry.rank_tuple] for custom sorting, read off the entry from [`Player.get_solo_rank()`][nexar.models.player.Player.get_solo_rank].

```py
--8<-- "examples/league_comparison.py"
```
