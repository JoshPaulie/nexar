# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

## [1.1.0] - 2026-05-17

> [!WARNING]
> This release includes breaking changes. Please review the "Changed" section carefully before upgrading. [^1]

### Added

- `get_riot_account_by_puuid(puuid, *, region)` — new public client method for account lookup by PUUID.
- `get_player()` and `Player.create()` now accept three identification patterns:
  - `get_player(game_name="...", tag_line="...")` — by game name + tag line (unchanged)
  - `get_player(puuid="...")` — by PUUID
  - `get_player(riot_id="name#tag")` — by Riot ID string
- Gracefully handle unknown `Queue` and `MapId` enum values from the Riot API.
- Add `Participant.kda()`. Not all matches return a participant's "challenges", despite participants from matches of all gamemodes having kills, deaths, and assists. This is a useful convenience method for a common statistic. By default it returns a ratio float, but can return a formatted string if `as_str=True` is passed (e.g. "10/2/5").

### Changed

- **Breaking:** `get_player()` and `Player.create()` are now keyword-only. Use `get_player(game_name="...", tag_line="...")` instead of `get_player("...", "...")`.
- **Breaking:** Remove `Participant.kda_string` property. Use `Participant.kda(as_str=True)` instead.

### Fixed

- Make `challenges`, `perks`, and `missions` fields optional on `Participant` to prevent deserialization errors.

### Wrapped API Endpoints

- **Account API**
  - `GET /riot/account/v1/accounts/by-puuid/{puuid}` → `RiotAccount` (via `get_riot_account_by_puuid`)

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

---

[^1]: Pretending to have users is fun :)
