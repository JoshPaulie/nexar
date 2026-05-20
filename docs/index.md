# Nexar

Dead simple League of Legend API lookups. Match history, solo/flex queue ranks, champion performance stats, all in a few lines of code.

Async, Pythonic, League-only, built-in rate limiting and disk caching.

[Quick start](./quick_start.md){ .md-button .md-button--primary }

## Objective

Nexar is an opinionated SDK for personal or small-scale League of Legends projects. It prioritizes developer experience and domain modeling over raw API access.

I built Nexar because I wanted a League-specific library that just works for my friend group's Discord bot.

- Simple summoner and match lookups (like op.gg)
- League centric (no TFT)
- Leaky bucket rate limiting via aiolimiter
- SQLite disk caching
- Fully type hinted with high-level objects
