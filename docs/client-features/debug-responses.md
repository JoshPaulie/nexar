# Debug API Responses

Nexar includes a debug feature to inspect API responses as they return from Riot. This is useful for troubleshooting and understanding response structures.

## Enabling Debug Output

Set the `NEXAR_DEBUG_RESPONSES` environment variable:

```bash
export NEXAR_DEBUG_RESPONSES=1
```

Or in Python:

```python
import os
os.environ["NEXAR_DEBUG_RESPONSES"] = "1"
```

## Debug Output Format

When enabled, the client prints detailed information about each API response:

```
============================================================
DEBUG: API Response for /riot/account/v1/accounts/by-riot-id/bexli/bex
URL: https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/bexli/bex
Status: 200
From Cache: True
Params: {"count": 10, "queue": 420}
Response Data:
{
  "puuid": "0wKS4sQQTcA6mAmu_oW5rVhyxmWAXV9hZrraXnDdh8GvelgGWYM5tM7fcHw0kalBVgCl6MxOZe0bLA",
  "gameName": "bexli",
  "tagLine": "bex"
}
============================================================
```

Output includes:

- Endpoint: The API endpoint path
- URL: The full URL including region
- Status: HTTP status code
- From Cache: Whether the response was served from cache
- Params: Query parameters sent with the request
- Response Data: The JSON response, formatted for readability
