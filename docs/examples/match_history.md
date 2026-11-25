# Match History

Get a Player's recent match history, with filters like queue type, dates, count, and a start offset for paging.

[`Player.get_matches()`][nexar.models.player.Player.get_matches] returns the matches themselves, not just their ids: one request for the id list, then one request per match. `count` caps at 100, so walk a long history by stepping `start` by `count` each page (the example shows the first two pages), and pass `allow_partial=True` when one failed id should not sink the page.

```py
--8<-- "examples/all_examples.py:match-history-demo"
```

[`to_dict()`][nexar.utils.to_dict] turns the returned model tree into JSON-safe values, enums included. Fields: [`Match`][nexar.models.match.match.Match], [`Participant`][nexar.models.match.participant.Participant].