# Logging

Nexar uses Python's standard `logging` module under the `"nexar"` logger name. All API calls, rate limit events, cache operations, and errors are logged, giving you visibility into the client's behavior.

## Basic Logging

Enable INFO-level logging to see API calls and statistics:

```python
-8<-- "client-features/logging.py:basic-logging"
```

### Example Output

```
API Call #1: /riot/account/v1/accounts/by-riot-id/bexli/bex (region: na1)
  Success (Status: 200, fresh)
```

## Verbose Logging

Enable DEBUG-level logging for detailed output including rate limiter decisions and cache hits:

```python
-8<-- "client-features/logging.py:verbose-logging"
```

### Example Output

```
2026-05-16 12:00:00,123 [nexar] INFO: API Call #1: /riot/account/v1/accounts/by-riot-id/bexli/bex (region: na1)
2026-05-16 12:00:00,456 [nexar] INFO:   Success (Status: 200, from cache)
```

## Suppress Logging

To silence nexar logging entirely:

```python
-8<-- "client-features/logging.py:suppress-logging"
```

## Custom Log Handler

Route nexar logs to a file or integrate with your application's logging setup:

```python
-8<-- "client-features/logging.py:custom-handler"
```

## Log Levels

The `"nexar"` logger emits messages at the following levels:

| Level     | Used For                                                      |
| --------- | ------------------------------------------------------------- |
| `DEBUG`   | Rate limiter decisions, method ID extraction, cache internals |
| `INFO`    | API calls, response status, cache management, call stats      |
| `WARNING` | Transient request retries (network errors, timeouts)          |
| `ERROR`   | Non-retryable request failures and API exceptions             |
