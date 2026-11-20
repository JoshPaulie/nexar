# Rate limiting

The limiter mirrors Riot's documented enforcement directly: a sliding-window
log per region, one window per configured application limit. Pass custom
application limits via `NexarClient(app_rate_limits=...)`.

::: nexar.rate_limiter.RateLimiter

::: nexar.rate_limiter.PERSONAL_LIMITS

::: nexar.rate_limiter.PRODUCTION_LIMITS
