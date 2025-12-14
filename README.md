# WhatsApp Wrapped 📊

Create beautiful Spotify Wrapped-style visualizations for your WhatsApp group chats! Analyze your chat activity, discover patterns, and generate stunning HTML/PDF reports with a sleek terminal aesthetic.

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
</p>

<p align="center">
  <a href="https://colab.research.google.com/github/Duelion/whatsapp-wrapped/blob/main/whatsapp_wrapped.ipynb" target="_blank">
    <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab" height="28">
  </a>
  &nbsp;&nbsp;
  <a href="https://buymeacoffee.com/duelion" target="_blank" rel="noopener noreferrer">
    <img src="https://cdn.buymeacoffee.com/buttons/v2/default-red.png" alt="Buy Me A Coffee" width="150">
  </a>
</p>

## ✨ Features

- **📈 Rich Analytics**: Message counts, activity patterns, emoji usage, and more
- **🎨 Beautiful Visualizations**: Interactive Plotly charts with a modern dark theme
- **👥 User Insights**: Top contributors, activity sparklines, hourly patterns
- **📅 Calendar Heatmaps**: Visualize activity across the entire year
- **💬 Message Analysis**: Word clouds, response times, conversation dynamics
- **📄 Multiple Formats**: Generate HTML reports and optional PDFs
- **🔒 Privacy-First**: All processing happens locally on your machine

## 🚀 Quick Start

### Option 1: Google Colab (No Installation Required)

The easiest way to use WhatsApp Wrapped - no installation needed!

<a href="https://colab.research.google.com/github/Duelion/whatsapp-wrapped/blob/main/whatsapp_wrapped.ipynb" target="_blank">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab" height="32">
</a>

1. Click the button above to open the notebook in Google Colab
2. Run the setup cell to install dependencies
3. Configure your options (year filter, minimum messages)
4. Upload your WhatsApp chat export
5. Download your beautiful report!

### Option 2: Local Installation

1. **Install uv** (fast Python package manager):

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

2. **Clone and install the project**:

```bash
git clone https://github.com/yourusername/whatsapp-wrapped.git
cd whatsapp-wrapped

# Install dependencies
uv sync
```

### Usage

1. **Export your WhatsApp chat**:
   - Open WhatsApp and navigate to the group chat
   - Tap the group name → More → Export chat
   - Choose "Without Media" for faster processing
   - Save the `.zip` file

2. **Generate your report**:

```bash
# Basic usage (creates HTML in current directory)
uv run whatsapp-wrapped chat.zip

# Generate both HTML and PDF
uv run whatsapp-wrapped chat.zip --pdf

# Save to specific directory
uv run whatsapp-wrapped chat.zip --output reports/

# Filter to specific year
uv run whatsapp-wrapped chat.zip --year 2024

# Custom report name
uv run whatsapp-wrapped chat.zip --name "My Group 2024"

# Quiet mode (no progress messages)
uv run whatsapp-wrapped chat.zip --quiet

# See all options
uv run whatsapp-wrapped --help
```

## 📖 CLI Options

```
whatsapp-wrapped <chat_file> [OPTIONS]

Arguments:
  chat_file              Path to WhatsApp chat export (.zip or .txt)

Options:
  -o, --output PATH      Output directory or file path (default: current directory)
  --pdf                  Also generate PDF report
  --year YEAR            Filter messages to a specific year
  --min-messages N       Minimum messages per user to include (default: 2)
  --name NAME            Custom name for the report file (default: chat filename)
  --fixed-layout         Force desktop layout on all devices
  -q, --quiet            Suppress progress messages
  --version              Show version number and exit
  -h, --help             Show help message and exit
```

## 📊 Example Output

The report includes:

- **Overview Stats**: Total messages, date range, member count
- **Top Contributors**: Bar chart of most active users
- **Activity Timeline**: Message volume over time
- **Calendar Heatmap**: Daily activity visualization
- **Hour of Day**: When is the chat most active?
- **Day of Week**: Which days are busiest?
- **User Details**: Per-user stats with activity sparklines
- **Emoji Leaders**: Top emoji users
- **Response Patterns**: Conversation dynamics

## 🛠️ Tech Stack

- **Python 3.10+**: Modern Python with type hints
- **uv**: Fast package management and execution
- **pandas**: Data manipulation and analysis
- **Plotly**: Interactive visualizations
- **Jinja2**: HTML template rendering
- **Playwright**: PDF generation with Chromium (optional)
- **Ruff**: Lightning-fast linting and formatting

## 📁 Project Structure

```
whatsapp-wrapped/
├── src/
│   ├── parser.py         # WhatsApp chat parsing
│   ├── analytics.py      # Data analysis
│   ├── charts.py         # Plotly visualizations
│   ├── generator.py      # Report generation (CLI entry point)
│   └── templates/
│       └── report.html   # Report template
├── tests/                # Test suite
├── config/
│   └── config.yaml       # Configuration example
├── pyproject.toml        # Project metadata and dependencies
├── README.md             # This file
└── CONTRIBUTING.md       # Development guide
```

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/whatsapp-wrapped.git
cd whatsapp-wrapped

# Install with development dependencies
uv sync --dev

# Run tests
uv run pytest

# Lint and format
uv run ruff check --fix src/
uv run ruff format src/
```

## 🔒 Privacy & Security

**Your data stays on your device.** This tool:

- ✅ Processes everything locally
- ✅ Never uploads your chats anywhere
- ✅ Never connects to the internet (except for package installation)
- ✅ Generates reports on your machine only

**Important**: Never commit actual chat exports to version control or share them publicly!

## 📝 Configuration

You can customize the analysis using `config/config.yaml`:

```yaml
analysis:
  year: 2024
  top_n_users: 10
  top_n_words: 50
  top_n_emojis: 20

theme:
  color_scheme: "spotify"
  primary_color: "#1DB954"

privacy:
  anonymize_names: false  # Replace names with "User 1", "User 2", etc.
```

## 🐛 Troubleshooting

### PDF Generation Issues

PDF generation uses Playwright with Chromium to render the HTML exactly as it appears in a browser.

If PDF generation fails:

```bash
# Install Playwright
uv add playwright

# Install Chromium browser (required for PDF generation)
playwright install chromium
```

The first time you run `playwright install chromium`, it will download the Chromium browser (~150MB). This is a one-time setup.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

Inspired by Spotify Wrapped and the desire to celebrate our digital conversations!

## 📞 Support

- 🐛 [Report Issues](https://github.com/yourusername/whatsapp-wrapped/issues)
- 💡 [Feature Requests](https://github.com/yourusername/whatsapp-wrapped/issues)
- 📖 [Documentation](https://github.com/yourusername/whatsapp-wrapped)

---

Made with ❤️ for WhatsApp users who love data
