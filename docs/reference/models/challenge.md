# Challenge API

The account-wide challenge system, via the lol-challenges-v1 ops, all six
route per-platform (`na1.api.riotgames.com`, like summoner and mastery; the
regional hosts answer 403 for this family, measured 2026-11-21). Distinct from
the [match Challenges model][nexar.models.match.challenges.Challenges], which is the per-match challenge
stats inside a match payload.

- [`NexarClient.get_all_challenge_configs()`][nexar.client.NexarClient.get_all_challenge_configs] / [`get_challenge_config(id)`][nexar.client.NexarClient.get_challenge_config],
  the challenge catalog, typed as [`ChallengeConfig`][nexar.models.challenge.ChallengeConfig] (405 challenges on NA at
  recording; the wire sends id, localizedNames, state, leaderboard, and
  thresholds on every entry, plus endTimestamp on exactly one, challenge
  600012; the reference DTO table's tracking and startTimestamp never appear
  on the wire).
- [`NexarClient.get_all_challenge_percentiles()`][nexar.client.NexarClient.get_all_challenge_percentiles] /
  [`get_challenge_percentiles(id)`][nexar.client.NexarClient.get_challenge_percentiles], flat challengeId→level→percentile maps.
- [`NexarClient.get_challenge_leaderboard(id, level, limit=...)`][nexar.client.NexarClient.get_challenge_leaderboard], apex-level
  boards, typed as [`ChallengeLeaderboardEntry`][nexar.models.challenge.ChallengeLeaderboardEntry] entries with global,
  ascending positions.
- [`NexarClient.get_player_challenge_data(puuid)`][nexar.client.NexarClient.get_player_challenge_data] and the
  [`Player.get_challenge_data()`][nexar.models.player.Player.get_challenge_data] seam, typed as [`PlayerChallengeData`][nexar.models.challenge.PlayerChallengeData].

::: nexar.models.challenge.ChallengeConfig
::: nexar.models.challenge.LocalizedChallengeNames
::: nexar.models.challenge.ChallengeLeaderboardEntry
::: nexar.models.challenge.PlayerChallengeData
::: nexar.models.challenge.ChallengeProgress
::: nexar.models.challenge.ChallengePoints
::: nexar.models.challenge.ChallengePreferences
