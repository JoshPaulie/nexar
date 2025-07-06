# Debug API Responses

The Nexar client includes a debug feature that allows you to inspect API responses as they are returned from the Riot Games API. This is useful for development, troubleshooting, and understanding the structure of API responses.

## Enabling Debug Output

To enable debug output, set the `NEXAR_DEBUG_RESPONSES` environment variable to any non-empty value:

```bash
export NEXAR_DEBUG_RESPONSES=1
```

Or in Python:

```python
import os
os.environ["NEXAR_DEBUG_RESPONSES"] = "1"
```

## Debug Output Format

When enabled, the debug feature will print detailed information about each API response:

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

The debug output includes:

- **Endpoint**: The API endpoint path that was called
- **URL**: The full URL including region
- **Status**: HTTP status code of the response
- **From Cache**: Whether the response was served from cache or was a fresh API call
- **Params**: Query parameters sent with the request (if any)
- **Response Data**: The full JSON response from the API, formatted for readability
