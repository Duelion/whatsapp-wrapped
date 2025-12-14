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

**IMPORTANT**: Test data files are NOT committed to the repository for privacy reasons.
You need to provide your own chat export file in `tests/data/` directory to run tests.

Tests automatically use the chat data file located in `tests/data/` directory. 
The test will find any `.zip` or `.txt` file in that directory (there should only be one).

**ALWAYS use `uv run` for running tests**:

```bash
# Run all tests
uv run pytest

# Run all tests with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_parser.py -v

# Run tests in a specific directory
uv run pytest tests/ -v

# Run with coverage report
uv run pytest --cov=src --cov-report=html

# Run with coverage and save to htmlcov/ directory
uv run pytest --cov=src --cov-report=html --cov-report=term
```

**Test Coverage:**
- `test_parser.py` - Parser functionality, message type classification, filtering
- `test_analytics.py` - Analytics engine, user stats, time patterns, emoji extraction
- `test_cli.py` - CLI argument parsing, all command-line options and flags

### Generate Test Report

To generate a test report using the test data for a specific year:

**Note**: Test data files are gitignored for privacy. Place your own chat export in `tests/data/` for testing.

```bash
# Generate report for year 2025 using test data (use actual filename)
uv run python -m src.generator "tests/data/your-chat-file.zip" --year 2025

# Or if using a .txt file
uv run python -m src.generator "tests/data/your-chat-file.txt" --year 2025

# Generate with PDF
uv run python -m src.generator "tests/data/your-chat-file.zip" --year 2025 --pdf
```

Generated test reports will be saved in the project root and are automatically gitignored.

**Note**: Keep only one chat file (`.zip` or `.txt`) in `tests/data/` directory for testing.
**NEVER commit chat files** - they contain private conversations!

### Test Results Location

Test results and coverage reports are saved to:
- **Coverage HTML reports**: `htmlcov/` directory
- **Coverage data**: `.coverage` file
- **Pytest cache**: `.pytest_cache/` directory

These directories are already gitignored.

### Install Dependencies

Dependencies are automatically installed when using `uv run`. To manually sync:

```bash
uv sync
```

## Important Notes

- **Always use `uv run`** - This ensures dependencies are properly managed and isolated
- `uv` automatically installs missing packages when using `uv run`
- The project requires Python 3.10 or higher
