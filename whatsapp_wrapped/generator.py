"""
WhatsApp Wrapped Report Generator

Main entry point for generating HTML and PDF reports from WhatsApp chat exports.
"""

import argparse
import asyncio
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import nest_asyncio
from jinja2 import Environment, FileSystemLoader

from .analytics import ChatAnalytics, analyze_chat, calculate_badges, format_hour, get_hour_emoji
from .charts import (
    ChartCollection,
    chart_to_html,
    create_user_hourly_sparkline,
    create_user_sparkline,
)
from .parser import ChatMetadata, parse_whatsapp_export


@dataclass
class ReportData:
    """Container for all data needed to generate a report."""

    metadata: ChatMetadata
    analytics: ChatAnalytics
    charts_html: dict[str, str]
    user_sparklines: dict[str, str]
    user_hourly_sparklines: dict[str, str]
    user_badges: dict[str, list[dict]]
    formatted_hour: str
    hour_emoji: str


def get_template_dir() -> Path:
    """Get the path to the templates directory."""
    return Path(__file__).parent / "templates"


def _render_report_template(
    report_data: ReportData, fixed_layout: bool = False, quiet: bool = False
) -> str:
    """
    Render the report HTML template with the given data.

    Args:
        report_data: ReportData containing all report information
        fixed_layout: Whether to force desktop layout on all devices
        quiet: Whether to suppress progress messages

    Returns:
        Rendered HTML content as string
    """
    # Set up Jinja2 environment
    template_dir = get_template_dir()
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=False,
    )
    template = env.get_template("report.html")

    # Render template
    if not quiet:
        print("[*] Rendering HTML report...")

    return template.render(
        metadata=report_data.metadata,
        analytics=report_data.analytics,
        charts=report_data.charts_html,
        user_sparklines=report_data.user_sparklines,
        user_hourly_sparklines=report_data.user_hourly_sparklines,
        user_badges=report_data.user_badges,
        generation_date=datetime.now().strftime("%B %d, %Y at %I:%M %p"),
        fixed_layout=fixed_layout,
        formatted_hour=report_data.formatted_hour,
        hour_emoji=report_data.hour_emoji,
    )


def _generate_report_data(
    chat_file: str | Path,
    year_filter: int | None = None,
    min_messages: int = 2,
    quiet: bool = False,
) -> ReportData:
    """
    Parse chat and generate all analytics, charts, and template data.

    Returns:
        ReportData object containing all report generation data
    """
    chat_file = Path(chat_file)

    if not quiet:
        print(f"[*] Loading chat file: {chat_file.name}")

    # Parse the chat
    df, metadata = parse_whatsapp_export(
        chat_file,
        filter_system=True,
        min_messages=min_messages,
        year_filter=year_filter,
    )

    if not quiet:
        print(f"[+] Parsed {len(df)} messages from {metadata.total_members} members")

    # Run analytics
    if not quiet:
        print("[*] Running analytics...")
    analytics = analyze_chat(df)

    # Generate charts
    if not quiet:
        print("[*] Generating charts...")
    chart_collection = ChartCollection(analytics)
    charts_html = chart_collection.to_html_dict(include_plotlyjs_first=True)

    # Generate user sparklines
    if not quiet:
        print("[*] Generating user sparklines...")
    user_sparklines = {}
    user_hourly_sparklines = {}
    for user_stat in analytics.user_stats:
        sparkline_fig = create_user_sparkline(user_stat.daily_activity, user_stat.name)
        user_sparklines[user_stat.name] = chart_to_html(sparkline_fig, include_plotlyjs=False)

        hourly_sparkline_fig = create_user_hourly_sparkline(
            user_stat.hourly_activity, user_stat.name
        )
        user_hourly_sparklines[user_stat.name] = chart_to_html(
            hourly_sparkline_fig, include_plotlyjs=False
        )

    # Calculate user badges
    if not quiet:
        print("[*] Calculating achievement badges...")
    user_badges = calculate_badges(analytics.user_stats)

    # Format peak hour data
    formatted_hour = format_hour(analytics.most_active_hour)
    hour_emoji = get_hour_emoji(analytics.most_active_hour)

    return ReportData(
        metadata=metadata,
        analytics=analytics,
        charts_html=charts_html,
        user_sparklines=user_sparklines,
        user_hourly_sparklines=user_hourly_sparklines,
        user_badges=user_badges,
        formatted_hour=formatted_hour,
        hour_emoji=hour_emoji,
    )


def generate_html_report(
    chat_file: str | Path,
    output_path: str | Path | None = None,
    year_filter: int | None = None,
    min_messages: int = 2,
    report_name: str | None = None,
    quiet: bool = False,
) -> Path:
    """
    Generate an HTML report from a WhatsApp chat export.

    Args:
        chat_file: Path to the WhatsApp export (.zip or .txt)
        output_path: Path for the output HTML file (optional)
        year_filter: Filter messages to a specific year (optional)
        min_messages: Minimum messages per user to include
        report_name: Custom name for the report file (optional, defaults to chat filename)
        quiet: Suppress progress messages

    Returns:
        Path to the generated HTML file
    """
    chat_file = Path(chat_file)

    # Generate all report data
    report_data = _generate_report_data(chat_file, year_filter, min_messages, quiet)

    # Render template
    html_content = _render_report_template(report_data, fixed_layout=False, quiet=quiet)

    # Determine output path
    if output_path is None:
        stem = report_name.replace(" ", "_") if report_name else chat_file.stem.replace(" ", "_")
        output_path = Path.cwd() / f"{stem}_report.html"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write HTML file
    output_path.write_text(html_content, encoding="utf-8")
    if not quiet:
        print(f"[+] HTML report saved: {output_path}")

    return output_path


def generate_static_html(
    html_path: str | Path,
    output_path: str | Path | None = None,
    quiet: bool = False,
) -> Path:
    """
    Generate a static HTML report from an existing HTML report using Playwright.

    Uses a real WebKit browser to render the HTML with all charts, then captures
    the fully-rendered DOM as a self-contained static HTML file. The result doesn't
    require JavaScript to display charts.

    Args:
        html_path: Path to the HTML report
        output_path: Path for the output static HTML file (optional)
        quiet: Suppress progress messages

    Returns:
        Path to the generated static HTML file
    """

    async def _generate_static() -> Path:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            print("[!] Playwright not installed. Install with: uv add playwright")
            print("[!] Then run: playwright install webkit")
            raise

        html_path_resolved = Path(html_path).resolve()

        if not html_path_resolved.exists():
            raise FileNotFoundError(f"HTML file not found: {html_path_resolved}")

        # Determine output path
        nonlocal output_path
        if output_path is None:
            # Default: add _static suffix before .html
            stem = html_path_resolved.stem
            output_path = html_path_resolved.with_name(f"{stem}_static.html")
        else:
            output_path = Path(output_path).resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)

        if not quiet:
            print("[*] Converting to static HTML with Playwright...")

        async with async_playwright() as p:
            # Launch headless WebKit
            browser = await p.webkit.launch()

            # Use a wider viewport for better layout
            page = await browser.new_page(
                viewport={"width": 1400, "height": 800},
                device_scale_factor=2,
            )

            # Navigate to the HTML file
            file_url = html_path_resolved.as_uri()
            await page.goto(file_url)

            # Wait for the page to fully load
            await page.wait_for_load_state("networkidle")

            # Wait for Plotly to finish rendering all charts
            # This checks that: 1) Plotly is loaded, 2) all chart containers have rendered data
            await page.wait_for_function("""
                () => {
                    // Check if Plotly is loaded
                    if (typeof Plotly === 'undefined') return false;
                    
                    // Get all Plotly chart containers
                    const plots = document.querySelectorAll('.js-plotly-plot');
                    if (plots.length === 0) return false;
                    
                    // Check each plot has data (meaning it's fully rendered)
                    for (const plot of plots) {
                        if (!plot.data || !plot.layout) return false;
                        // Check that SVG is present (chart is actually drawn)
                        if (!plot.querySelector('svg.main-svg')) return false;
                    }
                    return true;
                }
            """, timeout=30000)

            # Force Plotly to redraw all charts to ensure annotations render
            await page.evaluate("""
                () => {
                    const plots = document.querySelectorAll('.js-plotly-plot');
                    plots.forEach(plot => {
                        if (window.Plotly && plot.data) {
                            Plotly.relayout(plot, {});
                        }
                    });
                }
            """)

            # Wait for relayout to complete by checking the plots are still valid
            await page.wait_for_function("""
                () => {
                    const plots = document.querySelectorAll('.js-plotly-plot');
                    for (const plot of plots) {
                        if (!plot.querySelector('svg.main-svg')) return false;
                    }
                    return true;
                }
            """, timeout=10000)

            # Get the fully rendered HTML content
            rendered_html = await page.content()

            await browser.close()

        # Clean up: Remove Plotly.js script tags (charts are now static SVG)
        # Remove CDN script tags for Plotly
        rendered_html = re.sub(
            r'<script[^>]*src=["\']https://cdn\.plot\.ly/plotly[^"\']*["\'][^>]*></script>',
            "",
            rendered_html,
            flags=re.IGNORECASE,
        )

        # Write the static HTML file
        output_path.write_text(rendered_html, encoding="utf-8")

        if not quiet:
            print(f"[+] Static HTML report saved: {output_path}")

        return output_path

    # Run the async function
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None:
        # Running inside an existing event loop (e.g., Jupyter/Colab)
        # Use nest_asyncio to allow nested async calls
        nest_asyncio.apply()
        # Use the existing loop instead of creating a new one
        return loop.run_until_complete(_generate_static())
    else:
        # No existing loop - create a new one (normal CLI usage)
        return asyncio.run(_generate_static())


def generate_full_report(
    chat_file: str | Path,
    output_dir: str | Path | None = None,
    year_filter: int | None = None,
    min_messages: int = 2,
    report_name: str | None = None,
    generate_static: bool = False,
    fixed_layout: bool = False,
    quiet: bool = False,
) -> tuple[Path, Path | None]:
    """
    Generate HTML and optionally static reports from a WhatsApp chat export.

    Args:
        chat_file: Path to the WhatsApp export (.zip or .txt)
        output_dir: Directory for output files (optional)
        year_filter: Filter messages to a specific year (optional)
        min_messages: Minimum messages per user to include
        report_name: Custom name for the report file (optional, defaults to chat filename)
        generate_static: Whether to also generate static HTML (no JavaScript)
        fixed_layout: Force desktop layout on all devices
        quiet: Suppress progress messages

    Returns:
        Tuple of (html_path, static_path or None)
    """
    chat_file = Path(chat_file)

    # Generate all report data
    report_data = _generate_report_data(chat_file, year_filter, min_messages, quiet)

    # Determine output paths
    if output_dir is None:
        output_dir = Path.cwd()
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    stem = report_name.replace(" ", "_") if report_name else chat_file.stem.replace(" ", "_")
    html_path = output_dir / f"{stem}_report.html"
    static_path = output_dir / f"{stem}_report_static.html" if generate_static else None

    # Render HTML template
    html_content = _render_report_template(report_data, fixed_layout=fixed_layout, quiet=quiet)

    # Write HTML file
    html_path.write_text(html_content, encoding="utf-8")
    if not quiet:
        print(f"[+] HTML report saved: {html_path}")

    # Generate static HTML if requested
    if generate_static and static_path:
        try:
            generate_static_html(html_path, static_path, quiet=quiet)
        except ImportError:
            if not quiet:
                print("[!] Skipping static HTML generation (Playwright not available)")
                print("[!] Install with: uv add playwright && playwright install webkit")
            static_path = None
        except Exception as e:
            if not quiet:
                print(f"[!] Static HTML generation failed: {e}")
            static_path = None

    return html_path, static_path


def main():
    """Command-line interface for the report generator."""
    from . import __version__

    parser = argparse.ArgumentParser(
        description="Generate WhatsApp Wrapped reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  whatsapp-wrapped chat.zip
  whatsapp-wrapped chat.txt --output reports/
  whatsapp-wrapped chat.zip --static --year 2024
  whatsapp-wrapped chat.zip --name "My Group 2024" --year 2024
  whatsapp-wrapped chat.zip --quiet
        """,
    )

    parser.add_argument(
        "chat_file",
        help="Path to WhatsApp chat export (.zip or .txt)",
    )

    parser.add_argument(
        "-o",
        "--output",
        help="Output directory or file path (default: current directory)",
        default=None,
    )

    parser.add_argument(
        "--static",
        action="store_true",
        help="Generate static HTML with pre-rendered charts (no JavaScript required)",
    )

    parser.add_argument(
        "--year",
        type=int,
        help="Filter messages to a specific year",
        default=None,
    )

    parser.add_argument(
        "--min-messages",
        type=int,
        help="Minimum messages per user to include (default: 2)",
        default=2,
    )

    parser.add_argument(
        "--name",
        help="Custom name for the report file (default: chat filename)",
        default=None,
    )

    parser.add_argument(
        "--fixed-layout",
        action="store_true",
        help="Force desktop layout on all devices (no responsive scaling)",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress progress messages",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"whatsapp-wrapped {__version__}",
        help="Show version number and exit",
    )

    args = parser.parse_args()

    # Check if chat file exists
    chat_file = Path(args.chat_file)
    if not chat_file.exists():
        print(f"[!] Error: Chat file not found: {chat_file}")
        sys.exit(1)

    if not args.quiet:
        print()
        print("=" * 60)
        print("  WHATSAPP WRAPPED - REPORT GENERATOR")
        print("=" * 60)
        print()

    try:
        html_path, static_path = generate_full_report(
            chat_file=chat_file,
            output_dir=args.output,
            year_filter=args.year,
            min_messages=args.min_messages,
            report_name=args.name,
            generate_static=args.static,
            fixed_layout=args.fixed_layout,
            quiet=args.quiet,
        )

        if not args.quiet:
            print()
            print("=" * 60)
            print("  GENERATION COMPLETE")
            print("=" * 60)
            print()
            print(f"  HTML: {html_path}")
            if static_path:
                print(f"  Static HTML: {static_path}")
            print()

    except Exception as e:
        print(f"\n[!] Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
