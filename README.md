<p align="center">
  <img src=".github/assets/ws_logo.png" alt="WhatsApp Wrapped Logo" width="700">
</p>

<p align="center">
  <strong>Create beautiful Spotify Wrapped-style visualizations for your WhatsApp group chats!</strong>
</p>

<p align="center">
  <a href="https://github.com/Duelion/whatsapp-wrapped/stargazers"><img src="https://img.shields.io/github/stars/Duelion/whatsapp-wrapped?style=flat-square&color=yellow" alt="Stars"></a>
  <a href="https://github.com/Duelion/whatsapp-wrapped/blob/main/LICENSE"><img src="https://img.shields.io/github/license/Duelion/whatsapp-wrapped?style=flat-square" alt="License"></a>
  <img src="https://img.shields.io/badge/python-3.10+-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
</p>

<p align="center">
  <a href="https://duelion.github.io/whatsapp-wrapped/sample_report.html">
    <img src="https://img.shields.io/badge/🔍_View_Live_Sample_Report-4CAF50?style=for-the-badge&logoColor=white" alt="View Sample Report">
  </a>
</p>

---

<p align="center">
  <img src=".github/assets/hero_image.png" alt="WhatsApp Wrapped Preview" width="700">
</p>

---

## ✨ Features

| | | |
|:---:|:---:|:---:|
| 📈 **Rich Analytics** | 🎨 **Interactive Charts** | 👥 **User Insights** |
| Message counts, patterns & emoji stats | Beautiful Plotly visualizations | Top contributors & activity sparklines |
| 📅 **Calendar Heatmaps** | 📄 **Multiple Formats** | 🔒 **100% Private** |
| Year-at-a-glance activity view | HTML (Desktop), Static HTML (Mobile) | All processing stays on your device |

---

## 🚀 Get Started in 60 Seconds

### Option 1: Google Colab (Recommended)

Zero installation required — just upload your chat and get your report!

<p align="center">
  <a href="https://colab.research.google.com/github/Duelion/whatsapp-wrapped/blob/main/whatsapp_wrapped.ipynb">
    <img src="https://img.shields.io/badge/Open_in-Google_Colab-F9AB00?style=for-the-badge&logo=googlecolab&logoColor=white" alt="Open In Colab">
  </a>
</p>

### Option 2: Local Installation

```bash
# 1. Clone the project
git clone https://github.com/Duelion/whatsapp-wrapped.git && cd whatsapp-wrapped

# 2. Generate your report (uv auto-installs dependencies)
uv run whatsapp-wrapped your-chat.zip
```

> 💡 Don't have `uv`? Install it: `curl -LsSf https://astral.sh/uv/install.sh | sh` (macOS/Linux) or `irm https://astral.sh/uv/install.ps1 | iex` (Windows)

**Available Options:**
- `--name "My Group 2024"` - Custom report name and title displayed in the report
- `--year 2024` - Filter messages to a specific year
- `--static` - Generate mobile-friendly static HTML (requires optional `static` dependencies)
- `--output reports/` - Custom output directory
- `--quiet` - Suppress progress messages
- `--help` - Show all available options

#### Optional: Static HTML Generation

For mobile-friendly reports that work without JavaScript, install the optional static HTML dependencies:

```bash
# Install with static HTML support
uv pip install -e ".[static]"

# Install Playwright's WebKit browser
playwright install webkit
```

The `--static` flag will then generate a pre-rendered HTML file perfect for mobile devices.

> 💡 **Note:** On Linux, Playwright may require system dependencies. If you see a warning about missing dependencies, run: `sudo playwright install-deps webkit`

---

## 📱 How to Export Your WhatsApp Chat

1. Open WhatsApp → Go to your group chat
2. Tap the group name → **More** → **Export chat**
3. Choose **"Without Media"** for faster processing
4. Save the `.zip` file and use it with WhatsApp Wrapped!

---

## 🔒 Privacy First

Your conversations never leave your device. WhatsApp Wrapped:
- ✅ Runs entirely offline (after install)
- ✅ Never uploads or shares your data
- ✅ Generates reports locally

---

## 📦 Installation Options

### Basic Installation (Recommended)

The basic installation includes everything you need for interactive HTML reports:

```bash
# Using pip
pip install git+https://github.com/Duelion/whatsapp-wrapped.git

# Using uv (faster)
uv pip install git+https://github.com/Duelion/whatsapp-wrapped.git
```

### With Optional Features

**Static HTML Generation** - For mobile-friendly reports without JavaScript:

```bash
pip install "git+https://github.com/Duelion/whatsapp-wrapped.git#egg=whatsapp-wrapped[static]"
playwright install webkit
```

**Development** - For contributors:

```bash
pip install "git+https://github.com/Duelion/whatsapp-wrapped.git#egg=whatsapp-wrapped[dev]"
```

---

<p align="center">
  <a href="https://buymeacoffee.com/duelion">
    <img src="https://cdn.buymeacoffee.com/buttons/v2/default-red.png" alt="Buy Me A Coffee" width="150">
  </a>
</p>

<p align="center">
  <a href="https://github.com/Duelion/whatsapp-wrapped/issues">Report Bug</a> · 
  <a href="https://github.com/Duelion/whatsapp-wrapped/issues">Request Feature</a> · 
  <a href="https://github.com/Duelion/whatsapp-wrapped">⭐ Star this project</a>
</p>

<p align="center">
  Made with ❤️ for WhatsApp users who love data
</p>
