# Nexar

League of Legends SDK. Pythonic wrapper for Riot's LoL API.

## Development

### Running Tests

Tests use real Riot API calls rather than mocks. You'll need a valid Riot API key:

1. Copy `riot-key.sh.example` to `riot-key.sh`
2. Add your Riot API key to `riot-key.sh`
3. Run tests with the provided script:

```bash
./run_tests.sh
```

The script automatically sources your API key and runs the test suite.

### Test Requirements

- Valid Riot API key
- Active internet connection
- Tests may be rate-limited by Riot's API
