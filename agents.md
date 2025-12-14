# Agent Instructions

## Running the Project

This project uses `uv` for dependency management and running commands.

### Generate WhatsApp Wrapped Reports

Always use `uv run` to execute the generator:

```bash
# Basic usage
uv run python -m src.generator path/to/chat.zip

# Filter by year (e.g., 2025)
uv run python -m src.generator path/to/chat.zip --year 2025

# Generate PDF as well
uv run python -m src.generator path/to/chat.zip --year 2025 --pdf

# Specify output directory
uv run python -m src.generator path/to/chat.zip --output reports/

# Quiet mode (suppress progress messages)
uv run python -m src.generator path/to/chat.zip --quiet
```

### Run Tests

Use `uv run` for running tests:

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_parser.py

# Run with coverage
uv run pytest --cov=src
```

### Install Dependencies

Dependencies are automatically installed when using `uv run`. To manually sync:

```bash
uv sync
```

## Important Notes

- **Always use `uv run`** - This ensures dependencies are properly managed and isolated
- `uv` automatically installs missing packages when using `uv run`
- The project requires Python 3.10 or higher
