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

Tests automatically use the chat data file located in `tests/data/` directory. 
The test will find any `.zip` or `.txt` file in that directory (there should only be one).

Use `uv run` for running tests:

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_parser.py

# Run with verbose output
uv run pytest -v

# Run with coverage report
uv run pytest --cov=src --cov-report=html

# Run with coverage and save to htmlcov/ directory
uv run pytest --cov=src --cov-report=html --cov-report=term
```

### Generate Test Report

To generate a test report using the test data for a specific year:

```bash
# Generate report for year 2025 using test data (file name may vary)
uv run python -m src.generator "tests/data/WhatsApp Chat - Chicken Center.zip" --year 2025

# Or if using a .txt file
uv run python -m src.generator "tests/data/your-chat-file.txt" --year 2025

# Generate with PDF
uv run python -m src.generator "tests/data/WhatsApp Chat - Chicken Center.zip" --year 2025 --pdf
```

Generated test reports will be saved in the project root and are automatically gitignored.

**Note**: Keep only one chat file (`.zip` or `.txt`) in `tests/data/` directory for testing.

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
