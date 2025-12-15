<p align="center">
  <img src=".github/assets/ws_logo.png" alt="WhatsApp Wrapped Logo" width="700">
</p>

<p align="center">
  <strong>Create beautiful Spotify Wrapped-style visualizations for your WhatsApp group chats!</strong>
</p>

<p align="center">
  Analyze your chat activity, discover patterns, and generate stunning HTML/PDF reports with a sleek terminal aesthetic.
</p>

<p align="center">
  <a href="https://buymeacoffee.com/duelion" target="_blank" rel="noopener noreferrer">
    <img src="https://cdn.buymeacoffee.com/buttons/v2/default-red.png" alt="Buy Me A Coffee" width="150">
  </a>
</p>
<p align="center">
  <a href="https://duelion.github.io/whatsapp-wrapped/sample_report.html" target="_blank" rel="noopener noreferrer">
    [View Live Sample Report]
  </a>
</p>


---

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

<a href="https://colab.research.google.com/github/Duelion/whatsapp-wrapped/blob/main/whatsapp_wrapped.ipynb" target="_blank" rel="noopener noreferrer">
  <img src="https://img.shields.io/badge/Open_in-Google_Colab-F9AB00?style=for-the-badge&logo=googlecolab&logoColor=white" alt="Open In Colab">
</a>

1. Click the button above to open the notebook in Google Colab
2. **Step 1:** Run the setup cell to install dependencies
3. **Step 2:** Choose your output format (HTML only or HTML + PDF)
4. **Step 3:** Upload your WhatsApp chat export (.zip or .txt)
5. **Step 4:** Configure filters (year, users) and generate your report
6. Download your beautiful report!

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
git clone https://github.com/Duelion/whatsapp-wrapped.git
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
├── tests/                 # Test suite
├── config/
│   └── config.yaml        # Configuration example
├── whatsapp_wrapped.ipynb # Google Colab notebook
├── pyproject.toml         # Project metadata and dependencies
└── README.md              # This file
```

## 🔒 Privacy & Security

**Your data stays on your device.** This tool:

- ✅ Processes everything locally
- ✅ Never uploads your chats anywhere
- ✅ Never connects to the internet (except for package installation)
- ✅ Generates reports on your machine only

**Important**: Never commit actual chat exports to version control or share them publicly!


## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.


## 📞 Support

- 🐛 [Report Issues](https://github.com/Duelion/whatsapp-wrapped/issues)
- 💡 [Feature Requests](https://github.com/Duelion/whatsapp-wrapped/issues)
- ⭐ [Star the project](https://github.com/Duelion/whatsapp-wrapped) if you find it useful!

---

<p align="center">
  Made with ❤️ for WhatsApp users who love data
  <br><br>
  <a href="https://github.com/Duelion/whatsapp-wrapped">
    <img src="https://img.shields.io/github/stars/Duelion/whatsapp-wrapped?style=social" alt="GitHub Stars">
  </a>
</p>
