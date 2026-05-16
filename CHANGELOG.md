# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-05-14

Initial release.

### Added

- Persistent (SQLite) and in-memory caching for API responses with configurable TTLs and per-endpoint smart TTLs.
- In-memory rate limiter supporting app, method, and service limits per region, with per-region locking to prevent race conditions.
- Pre-configured rate limits for both personal and production API keys.
- Automatic retries for rate limit errors with Retry-After header parsing.
- Configurable HTTP timeout support exposed via `CacheConfig`.
- `BatchError` exception to collect and report all errors when using `get_players()`.
- `team_total_percentage()` utility function.
- Dataclasses for all API response models with type hints, docstrings, and helper methods.
- High-level `Player` object with lazy-loaded summoner, league entries, and match history.
- `ParticipantList` and `MatchList` specialized list classes with filtering and stats methods.
- `sort_players_by_rank()` utility for comparing players by ranked queue standing.
- Champion and performance stats aggregation.
- Convenience properties: `Participant.kda()`, `Participant.creep_score`, `Participant.champion_icon_url`, `Summoner.profile_icon_url`.
- `NEXAR_DEBUG_RESPONSES` environment variable for debugging API responses.

### Wrapped API Endpoints

- **Account API**
  - `GET /riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}` → `RiotAccount`
- **Summoner API**
  - `GET /lol/summoner/v4/summoners/by-puuid/{puuid}` → `Summoner`
- **League API**
  - `GET /lol/league/v4/entries/by-puuid/{puuid}` → `list[LeagueEntry]`
- **Match API**
  - `GET /lol/match/v5/matches/{match_id}` → `Match`
  - `GET /lol/match/v5/matches/by-puuid/{puuid}/ids` → `list[str]`
- **Convenience Methods**
  - `client.get_player(game_name, tag_line)` → `Player`
  - `client.get_players(riot_ids)` → `list[Player]`
