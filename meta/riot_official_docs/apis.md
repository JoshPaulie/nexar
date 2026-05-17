# Riot API Reference (Local Notes)

Source URL: https://developer.riotgames.com/apis

## Account-v1 core endpoints

- `GET /riot/account/v1/accounts/by-puuid/{puuid}`
- `GET /riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}`
- `GET /riot/account/v1/accounts/me`
- `GET /riot/account/v1/active-shards/by-game/{game}/by-puuid/{puuid}`
- `GET /riot/account/v1/region/by-game/{game}/by-puuid/{puuid}`

Routing note: account-v1 uses regional routing values (`americas`, `asia`, `europe`).

## League of Legends core endpoints

- `SUMMONER-V4`
- `MATCH-V5`
- `LEAGUE-V4`
- `LEAGUE-EXP-V4`
- `CHAMPION-MASTERY-V4`
- `CLASH-V1`
- `SPECTATOR-V5`
- `LOL-STATUS-V4`
- `LOL-CHALLENGES-V1`
- `TOURNAMENT-V5`
- `TOURNAMENT-STUB-V5`

## Notes

- For full operation-level schemas and response models, open the upstream API site directly.
- Keep this file as a local link target for other markdown docs in this repo.
