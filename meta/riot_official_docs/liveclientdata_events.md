# liveclientdata_events

Source URL: https://static.developer.riotgames.com/docs/lol/liveclientdata_events.json

Shape: object with `Events` array.

Common event names in sample data:

- `GameStart`
- `MinionsSpawning`
- `FirstBrick`
- `TurretKilled`
- `InhibKilled`
- `DragonKill`
- `HeraldKill`
- `BaronKill`
- `ChampionKill`
- `Multikill`
- `Ace`

Representative event structure:

```json
{
	"EventID": 0,
	"EventName": "ChampionKill",
	"EventTime": 0.0,
	"VictimName": "Riot Gene",
	"KillerName": "Riot Tuxedo",
	"Assisters": ["Player 1"]
}
```
