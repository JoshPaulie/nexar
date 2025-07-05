# Nexar Examples

This directory contains organized examples demonstrating how to use the Nexar SDK for League of Legends API access.

## Directory Structure

```
examples/
├── README.md                       # This file
├── basic/                          # Basic usage examples
│   ├── player_info.py             # Get basic player information
│   ├── match_history.py           # Retrieve match history
│   └── performance_analysis.py    # Analyze player performance
├── features/                       # Feature-specific examples
│   ├── caching.py                 # Caching configurations and usage
│   ├── rate_limiting.py           # Rate limiting demonstrations
│   └── api_monitoring.py          # API monitoring and logging
├── advanced/                       # Advanced analysis examples
│   ├── role_analysis.py           # Role-based performance analysis
│   ├── multi_player_comparison.py # Compare multiple players
│   └── challenges_analysis.py     # Match challenges analysis
└── api/                           # Low-level API examples
    ├── match_ids.py               # Direct match IDs API usage
    └── league_entries.py          # Direct league entries API usage
```

## Getting Started

All examples require a Riot Games API key set as an environment variable:

```bash
export RIOT_API_KEY="your_api_key_here"
```

### Running Examples

```bash
# Basic player information
python examples/basic/player_info.py

# Match history analysis
python examples/basic/match_history.py

# API monitoring demonstration
python examples/features/api_monitoring.py
```

## Testing Note

All examples use the test player "bexli#bex" as specified in the development guidelines. When adapting these examples, replace with your desired player names and tags.

## Need Help?

- Check the `/docs` directory for detailed documentation
- Review the source code in `/src/nexar` for implementation details
- All examples are self-contained and runnable
