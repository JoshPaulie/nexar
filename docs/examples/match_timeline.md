# Match Timeline

Replay a match minute by minute: a gold curve per player, and the full event stream (kills, items, wards, objectives) from `NexarClient.get_match_timeline()`.

Use the match's own id: fetch the match first and pass its id to `get_match_timeline()`. A timeline from any other match reads fine and means nothing.

```py
--8<-- "examples/match_timeline.py"
```
