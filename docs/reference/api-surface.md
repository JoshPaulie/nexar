# API Surface

Every Riot op Nexar wraps, with the method that wraps it and what you get back. `get_player` is the front door: it resolves an account by Riot ID or PUUID and hands back a [`Player`](models/player.md) that lazily fetches the rest (`player.get_summoner()`, `player.get_solo_rank()`, `player.get_matches()`). `get_players` does the same for a batch.

## Account & Summoner

| Endpoint | Method | Returns |
|----------|--------|---------|
| `GET /riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}` | `get_riot_account` | [`RiotAccount`](models/account.md) |
| `GET /riot/account/v1/accounts/by-puuid/{puuid}` | `get_riot_account_by_puuid` | [`RiotAccount`](models/account.md) |
| `GET /lol/summoner/v4/summoners/by-puuid/{puuid}` | `get_summoner_by_puuid` | [`Summoner`](models/account.md) |

## Ranked

| Endpoint | Method | Returns |
|----------|--------|---------|
| `GET /lol/league/v4/entries/by-puuid/{puuid}` | `get_league_entries_by_puuid` | [`list[LeagueEntry]`](models/league.md) |
| `GET /lol/league/v4/entries/{queue}/{tier}/{division}` | `get_league_entries` | [`list[LeagueEntry]`](models/league.md) |
| `GET /lol/league-exp/v4/entries/{queue}/{tier}/{division}` | `get_league_exp_entries` | [`list[LeagueEntry]`](models/league.md) |
| `GET /lol/league/v4/challengerleagues/by-queue/{queue}` | `get_challenger_league` | [`LeagueList`](models/league.md) |
| `GET /lol/league/v4/grandmasterleagues/by-queue/{queue}` | `get_grandmaster_league` | [`LeagueList`](models/league.md) |
| `GET /lol/league/v4/masterleagues/by-queue/{queue}` | `get_master_league` | [`LeagueList`](models/league.md) |

## Match

| Endpoint | Method | Returns |
|----------|--------|---------|
| `GET /lol/match/v5/matches/{matchId}` | `get_match` | [`Match`](models/match.md) |
| `GET /lol/match/v5/matches/by-puuid/{puuid}/ids` | `get_match_ids_by_puuid` | `list[str]` |
| `GET /lol/match/v5/matches/{matchId}/timeline` | `get_match_timeline` | [`Timeline`](models/match-timeline.md) |

## Champion Mastery

| Endpoint | Method | Returns |
|----------|--------|---------|
| `GET /lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/by-champion/{championId}` | `get_champion_mastery` | [`ChampionMastery`](models/champion-mastery.md) |
| `GET /lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}` | `get_champion_masteries` | [`list[ChampionMastery]`](models/champion-mastery.md) |
| `GET /lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/top` | `get_top_champion_masteries` | [`list[ChampionMastery]`](models/champion-mastery.md) |
| `GET /lol/champion-mastery/v4/scores/by-puuid/{puuid}` | `get_champion_mastery_score` | `int` |

## Platform

| Endpoint | Method | Returns |
|----------|--------|---------|
| `GET /lol/platform/v3/champion-rotations` | `get_champion_rotations` | [`ChampionRotations`](models/champion-rotations.md) |
| `GET /lol/status/v4/platform-data` | `get_platform_status` | [`PlatformStatus`](models/platform-status.md) |

## Challenges

| Endpoint | Method | Returns |
|----------|--------|---------|
| `GET /lol/challenges/v1/challenges/config` | `get_all_challenge_configs` | [`list[ChallengeConfig]`](models/challenge.md) |
| `GET /lol/challenges/v1/challenges/{challengeId}/config` | `get_challenge_config` | [`ChallengeConfig`](models/challenge.md) |
| `GET /lol/challenges/v1/challenges/percentiles` | `get_all_challenge_percentiles` | `dict[str, dict[str, float]]` |
| `GET /lol/challenges/v1/challenges/{challengeId}/percentiles` | `get_challenge_percentiles` | `dict[str, float]` |
| `GET /lol/challenges/v1/challenges/{challengeId}/leaderboards/by-level/{level}` | `get_challenge_leaderboard` | [`list[ChallengeLeaderboardEntry]`](models/challenge.md) |
| `GET /lol/challenges/v1/player-data/{puuid}` | `get_player_challenge_data` | [`PlayerChallengeData`](models/challenge.md) |
