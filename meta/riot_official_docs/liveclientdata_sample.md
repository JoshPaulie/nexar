# liveclientdata_sample

Source URL: https://static.developer.riotgames.com/docs/lol/liveclientdata_sample.json

Top-level shape:

- `activePlayer`
- `allPlayers`
- `events`
- `gameData`

Representative structure excerpt:

```json
{
	"activePlayer": {
		"abilities": {"Q": {}, "W": {}, "E": {}, "R": {}, "Passive": {}},
		"championStats": {},
		"fullRunes": {},
		"currentGold": 0,
		"level": 1,
		"summonerName": "Riot Tuxedo"
	},
	"allPlayers": [
		{
			"championName": "Annie",
			"team": "ORDER",
			"scores": {},
			"summonerSpells": {},
			"runes": {}
		}
	],
	"events": {"Events": []},
	"gameData": {"gameMode": "CLASSIC", "mapNumber": 11}
}
```
