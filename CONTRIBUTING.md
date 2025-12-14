# Contributing to WhatsApp Wrapped

Thank you for your interest in contributing! This document provides guidelines and setup instructions for developers.

## 🚀 Quick Setup

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

1. **Install uv**:

```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Clone and setup**:

```bash
git clone https://github.com/yourusername/whatsapp-wrapped.git
cd whatsapp-wrapped

# Install all dependencies (including dev dependencies)
uv sync --dev
```

## 🛠️ Development Workflow

### Package Management with uv

**Important**: This project uses `uv` exclusively for package management. Do NOT use `pip` or `uv pip`.

```bash
# Add a new dependency
uv add package-name

# Add a development dependency
uv add --dev package-name

# Remove a dependency
uv remove package-name

# Sync dependencies after pulling changes
uv sync --dev
```

**Why uv?**
- 10-100x faster than pip
- Better dependency resolution
- Automatic virtual environment management
- Keeps `pyproject.toml` and lockfile in sync

### Running Commands

Always use `uv run` to execute commands (no need to activate virtual environments):

```bash
# Run the CLI
uv run whatsapp-wrapped chat.zip

# Run tests
uv run pytest

# Run linter
uv run ruff check src/

# Format code
uv run ruff format src/
```

### Code Quality

This project uses [Ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Check for issues
uv run ruff check src/

# Auto-fix issues
uv run ruff check --fix src/

# Format code
uv run ruff format src/

# Run both checks and formatting
uv run ruff check --fix src/ && uv run ruff format src/
```

**Code Style Guidelines**:
- Line length: 100 characters
- Use double quotes for strings
- Follow PEP 8 conventions
- Add type hints where appropriate
- Write docstrings for public functions and classes

### Testing

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_parser.py

# Run with coverage report
uv run pytest --cov=src --cov-report=html
```

**Test Structure**:
- `tests/conftest.py` - Shared fixtures and configuration
- `tests/test_*.py` - Test modules

**Writing Tests**:
```python
def test_feature(chat_data_3months):
    """Test description following pytest conventions."""
    df, metadata = chat_data_3months
    
    # Your test logic
    assert expected == actual
```

## 📁 Project Structure

```
whatsapp-wrapped/
├── src/
│   ├── __init__.py       # Package exports and version
│   ├── parser.py         # WhatsApp chat parsing logic
│   ├── analytics.py      # Data analysis and statistics
│   ├── charts.py         # Plotly visualization generation
│   ├── generator.py      # Report generation and CLI
│   └── templates/
│       └── report.html   # Jinja2 HTML template
├── tests/                # Test suite
│   ├── conftest.py       # Pytest fixtures
│   └── test_*.py         # Test modules
├── config/
│   └── config.yaml       # Example configuration
├── pyproject.toml        # Project metadata and dependencies
├── uv.lock              # Locked dependency versions (commit this!)
├── README.md            # User documentation
└── CONTRIBUTING.md      # This file
```

## 🔧 Making Changes

### Before You Start

1. Create a new branch for your feature/fix:
```bash
git checkout -b feature/your-feature-name
```

2. Ensure dependencies are up to date:
```bash
uv sync --dev
```

### During Development

1. **Write clean code**: Follow the style guidelines above
2. **Add tests**: Cover new functionality with tests
3. **Update docs**: Update README or docstrings as needed
4. **Test locally**: Run tests and linting before committing

### Before Committing

```bash
# Run tests
uv run pytest

# Check and fix linting issues
uv run ruff check --fix src/ tests/

# Format code
uv run ruff format src/ tests/

# Verify everything passes
uv run ruff check src/ tests/
```

### Commit Guidelines

- Use clear, descriptive commit messages
- Follow conventional commits format (optional but encouraged):
  - `feat: Add new feature`
  - `fix: Fix bug in parser`
  - `docs: Update README`
  - `test: Add tests for analytics`
  - `refactor: Improve code structure`

## 🐛 Reporting Issues

When reporting bugs, please include:

1. **Description**: Clear description of the issue
2. **Steps to reproduce**: Minimal steps to reproduce the bug
3. **Expected behavior**: What you expected to happen
4. **Actual behavior**: What actually happened
5. **Environment**: OS, Python version, uv version
6. **Logs**: Relevant error messages or stack traces

**Note**: Never include actual WhatsApp chat data in bug reports!

## 💡 Feature Requests

We welcome feature requests! Please:

1. Check if the feature has already been requested
2. Describe the feature and its use case
3. Explain why it would be valuable
4. Provide examples if applicable

## 🔒 Privacy & Security

- **Never commit actual chat data** (`.zip` or `.txt` files)
- All data processing must happen locally
- No network requests during analysis (except package installation)
- Respect user privacy in all features

## 📚 Additional Resources

- [uv documentation](https://github.com/astral-sh/uv)
- [Ruff documentation](https://github.com/astral-sh/ruff)
- [Plotly documentation](https://plotly.com/python/)
- [pandas documentation](https://pandas.pydata.org/)
- [pytest documentation](https://docs.pytest.org/)

## 🎯 Areas for Contribution

Looking for where to contribute? Consider:

- **Parser improvements**: Support for different WhatsApp export formats
- **New visualizations**: Additional chart types or analytics
- **Performance**: Optimize parsing or chart generation
- **Documentation**: Improve docs, add examples, write tutorials
- **Tests**: Increase test coverage
- **Internationalization**: Multi-language support
- **Themes**: Additional color schemes or layouts

## 📝 Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what's best for the community
- Show empathy towards other contributors

## ❓ Questions?

Feel free to:
- Open an issue for discussion
- Ask in pull request comments
- Check existing issues and PRs

---

Thank you for contributing to WhatsApp Wrapped! 🎉
