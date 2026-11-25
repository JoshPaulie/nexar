# Challenge Stats

If there's a common stat you're curious about, it's likely in [`Participant.Challenges`][nexar.models.match.participant.Participant.challenges]! This has fun participant stats like vision score, damage share, and objective steals. You can access it like this:

```py
--8<-- "examples/challenge_stats.py"
```

The per-minute rates live here, not on [`Participant`][nexar.models.match.participant.Participant]: `gold_per_minute`, `damage_per_minute`, and `vision_score_per_minute`. `challenges` is `None` when Riot omits the block, which older matches do, so guard the read or fall back to a total divided by [`MatchInfo.game_duration`][nexar.models.match.match.MatchInfo.game_duration].
