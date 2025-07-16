# Nexar

Dead simple League of Legend API lookups. Match history, solo/flex queue ranks, champion performance stats, all in a few lines of code.

Async, pythonic, built-in rate limiting & disk caching.

[Quick start](./quick_start.md){ .md-button .md-button--primary }

## Inspiration

Nexar was created because I wanted the following from my League wrapper, particularly for my friend group's discord bot:

- Simple summoner and match lookups (like op.gg)
- League centric
- Basic rate limiting
- Caching
- Type hinted
- High level objects with methods like `.get_matches()`, and be returned actual Python objects
