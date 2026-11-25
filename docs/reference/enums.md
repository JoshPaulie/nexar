# Enums

All enums live in `nexar.enums` and are re-exported from the top-level `nexar` package.

## Display labels

Every enum prints as a human-readable label, not as its wire value: `str(Queue.SOLO_QUEUE)` is `'Ranked Solo 5x5'`, and `str(MatchParticipantPosition.UTILITY)` is `'Utility'`. The wire value stays on `.value` (`420`, `'UTILITY'`).

Compare with the member, never with `str()`: `participant.team_position == MatchParticipantPosition.UTILITY`, or `participant.team_position.value == "UTILITY"` when a string is what you need. A comparison against the uppercase token the field docs list (`"UTILITY"`) is false and matches nothing, with no error to tell you why.

::: nexar.enums.Region

::: nexar.enums.PlatformId

::: nexar.enums.RankTier

::: nexar.enums.RankDivision

::: nexar.enums.Queue

::: nexar.enums.MapId

::: nexar.enums.MatchType

::: nexar.enums.ChallengeLevel

::: nexar.enums.MatchParticipantPosition
