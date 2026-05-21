# Tests

## Running

```sh
just test       # mocked only (fast)
just test-full  # includes real Riot API calls (slow)
```

## Markers

| Marker | Description |
|--------|-------------|
| `slow` | Makes real Riot API calls. Skipped by `just test`. |

## Quota lock

Before `slow` tests run, the session fixture checks `/tmp/nexar-last-ran.txt`. If fewer than 125 seconds have elapsed since the last dogfood bowl or integration test run, it sleeps for the remainder — ensuring the rate limiter starts with a full quota window.
