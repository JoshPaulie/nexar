# Aliases
alias c := check
alias f := format
alias l := lint
alias m := mypy
alias t := test

# Run all quality checks: formatting, linting, type checking, and short tests
check: format lint mypy test

# Run ruff formatter
format:
    uv run ruff format src

# Run ruff linter with auto-fixes
lint:
    uv run ruff check --fix --unsafe-fixes src

# Run mypy type checker
mypy:
    uv run mypy 

# Source riot-key.sh
key:
    source ./riot-key.sh

# Run short test suite (mocked only, no real API calls)
test:
    source ./riot-key.sh && uv run pytest tests -q -m "not slow"

# Run full test suite including integration tests (makes real Riot API calls - slow)
test-full:
    source ./riot-key.sh && uv run pytest tests -q
