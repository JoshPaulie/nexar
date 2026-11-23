# API Surface

Every Riot op Nexar wraps, with the method that wraps it and what you get back. [`get_player`][nexar.client.NexarClient.get_player] is the front door: it resolves an account by Riot ID or PUUID and hands back a [`Player`][nexar.models.player.Player] that lazily fetches the rest ([`player.get_summoner()`][nexar.models.player.Player.get_summoner], [`player.get_solo_rank()`][nexar.models.player.Player.get_solo_rank], [`player.get_matches()`][nexar.models.player.Player.get_matches]). [`get_players`][nexar.client.NexarClient.get_players] does the same for a batch.

## Account & Summoner

| Endpoint | Method | Returns |
|----------|--------|---------|
| `GET /riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}` | [`get_riot_account`][nexar.client.NexarClient.get_riot_account] | [`RiotAccount`][nexar.models.account.RiotAccount] |
| `GET /riot/account/v1/accounts/by-puuid/{puuid}` | [`get_riot_account_by_puuid`][nexar.client.NexarClient.get_riot_account_by_puuid] | [`RiotAccount`][nexar.models.account.RiotAccount] |
| `GET /lol/summoner/v4/summoners/by-puuid/{puuid}` | [`get_summoner_by_puuid`][nexar.client.NexarClient.get_summoner_by_puuid] | [`Summoner`][nexar.models.account.Summoner] |

## Ranked

| Endpoint | Method | Returns |
|----------|--------|---------|
| `GET /lol/league/v4/entries/by-puuid/{puuid}` | [`get_league_entries_by_puuid`][nexar.client.NexarClient.get_league_entries_by_puuid] | [`list[LeagueEntry]`][nexar.models.league.LeagueEntry] |
| `GET /lol/league/v4/entries/{queue}/{tier}/{division}` | [`get_league_entries`][nexar.client.NexarClient.get_league_entries] | [`list[LeagueEntry]`][nexar.models.league.LeagueEntry] |
| `GET /lol/league-exp/v4/entries/{queue}/{tier}/{division}` | [`get_league_exp_entries`][nexar.client.NexarClient.get_league_exp_entries] | [`list[LeagueEntry]`][nexar.models.league.LeagueEntry] |
| `GET /lol/league/v4/challengerleagues/by-queue/{queue}` | [`get_challenger_league`][nexar.client.NexarClient.get_challenger_league] | [`LeagueList`][nexar.models.league.LeagueList] |
| `GET /lol/league/v4/grandmasterleagues/by-queue/{queue}` | [`get_grandmaster_league`][nexar.client.NexarClient.get_grandmaster_league] | [`LeagueList`][nexar.models.league.LeagueList] |
| `GET /lol/league/v4/masterleagues/by-queue/{queue}` | [`get_master_league`][nexar.client.NexarClient.get_master_league] | [`LeagueList`][nexar.models.league.LeagueList] |

## Match

| Endpoint | Method | Returns |
|----------|--------|---------|
| `GET /lol/match/v5/matches/{matchId}` | [`get_match`][nexar.client.NexarClient.get_match] | [`Match`][nexar.models.match.Match] |
| `GET /lol/match/v5/matches/by-puuid/{puuid}/ids` | [`get_match_ids_by_puuid`][nexar.client.NexarClient.get_match_ids_by_puuid] | `list[str]` |
| `GET /lol/match/v5/matches/{matchId}/timeline` | [`get_match_timeline`][nexar.client.NexarClient.get_match_timeline] | [`Timeline`][nexar.models.match.timeline.Timeline] |

## Champion Mastery

| Endpoint | Method | Returns |
|----------|--------|---------|
| `GET /lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/by-champion/{championId}` | [`get_champion_mastery`][nexar.client.NexarClient.get_champion_mastery] | [`ChampionMastery`][nexar.models.champion_mastery.ChampionMastery] |
| `GET /lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}` | [`get_champion_masteries`][nexar.client.NexarClient.get_champion_masteries] | [`list[ChampionMastery]`][nexar.models.champion_mastery.ChampionMastery] |
| `GET /lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/top` | [`get_top_champion_masteries`][nexar.client.NexarClient.get_top_champion_masteries] | [`list[ChampionMastery]`][nexar.models.champion_mastery.ChampionMastery] |
| `GET /lol/champion-mastery/v4/scores/by-puuid/{puuid}` | [`get_champion_mastery_score`][nexar.client.NexarClient.get_champion_mastery_score] | `int` |

## Platform

| Endpoint | Method | Returns |
|----------|--------|---------|
| `GET /lol/platform/v3/champion-rotations` | [`get_champion_rotations`][nexar.client.NexarClient.get_champion_rotations] | [`ChampionRotations`][nexar.models.champion_rotations.ChampionRotations] |
| `GET /lol/status/v4/platform-data` | [`get_platform_status`][nexar.client.NexarClient.get_platform_status] | [`PlatformStatus`][nexar.models.platform_status.PlatformStatus] |

## Challenges

| Endpoint | Method | Returns |
|----------|--------|---------|
| `GET /lol/challenges/v1/challenges/config` | [`get_all_challenge_configs`][nexar.client.NexarClient.get_all_challenge_configs] | [`list[ChallengeConfig]`][nexar.models.challenge.ChallengeConfig] |
| `GET /lol/challenges/v1/challenges/{challengeId}/config` | [`get_challenge_config`][nexar.client.NexarClient.get_challenge_config] | [`ChallengeConfig`][nexar.models.challenge.ChallengeConfig] |
| `GET /lol/challenges/v1/challenges/percentiles` | [`get_all_challenge_percentiles`][nexar.client.NexarClient.get_all_challenge_percentiles] | `dict[str, dict[str, float]]` |
| `GET /lol/challenges/v1/challenges/{challengeId}/percentiles` | [`get_challenge_percentiles`][nexar.client.NexarClient.get_challenge_percentiles] | `dict[str, float]` |
| `GET /lol/challenges/v1/challenges/{challengeId}/leaderboards/by-level/{level}` | [`get_challenge_leaderboard`][nexar.client.NexarClient.get_challenge_leaderboard] | [`list[ChallengeLeaderboardEntry]`][nexar.models.challenge.ChallengeLeaderboardEntry] |
| `GET /lol/challenges/v1/player-data/{puuid}` | [`get_player_challenge_data`][nexar.client.NexarClient.get_player_challenge_data] | [`PlayerChallengeData`][nexar.models.challenge.PlayerChallengeData] |
