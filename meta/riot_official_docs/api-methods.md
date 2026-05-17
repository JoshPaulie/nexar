# League Tournaments API Methods

Source URL: https://developer.riotgames.com/api-methods

The upstream `api-methods` page is JS-rendered and was not fully extractable via defuddle. This local file captures the tournament methods referenced by lol.md.

## League Tournaments API methods

- `POST /lol/tournament/v5/providers`
- `POST /lol/tournament/v5/tournaments`
- `POST /lol/tournament/v5/codes`
- `GET /lol/tournament/v5/codes/{tournamentCode}`
- `GET /lol/tournament/v5/codes/{tournamentCode}/lobby-events`

## Related method notes

- Lobby events endpoint is used to audit pre-game lobby activity.
- Tournament providers are strongly associated with API keys.
- Reusing a tournament code can make callback/match tracking less reliable.
