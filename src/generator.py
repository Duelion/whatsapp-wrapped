"""
WhatsApp Wrapped Report Generator

Main entry point for generating HTML and PDF reports from WhatsApp chat exports.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .analytics import analyze_chat
from .charts import ChartCollection
from .parser import parse_whatsapp_export


def get_template_dir() -> Path:
    """Get the path to the templates directory."""
    return Path(__file__).parent / "templates"


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

    if not quiet:
        print(f"[*] Loading chat file: {chat_file.name}")

    # Parse the chat
    df, metadata = parse_whatsapp_export(
        chat_file,
        filter_system=True,
        min_messages=min_messages,
        year_filter=year_filter,
    )

    print(f"[+] Parsed {len(df)} messages from {metadata.total_members} members")

    # Run analytics
    print("[*] Running analytics...")
    analytics = analyze_chat(df)

    # Generate charts
    print("[*] Generating charts...")
    chart_collection = ChartCollection(analytics)
    charts_html = chart_collection.to_html_dict(include_plotlyjs_first=True)  # top_users loads Plotly
    
    # Generate user sparklines
    print("[*] Generating user sparklines...")
    from .charts import create_user_sparkline, create_user_hourly_sparkline, chart_to_html
    user_sparklines = {}
    user_hourly_sparklines = {}
    for user_stat in analytics.user_stats:
        # Yearly activity sparkline - Plotly already loaded by top_users chart
        sparkline_fig = create_user_sparkline(user_stat.daily_activity, user_stat.name)
        user_sparklines[user_stat.name] = chart_to_html(sparkline_fig, include_plotlyjs=False)
        
        # Hourly pattern sparkline
        hourly_sparkline_fig = create_user_hourly_sparkline(user_stat.hourly_activity, user_stat.name)
        user_hourly_sparklines[user_stat.name] = chart_to_html(hourly_sparkline_fig, include_plotlyjs=False)

    # Calculate user badges
    if not quiet:
        print("[*] Calculating achievement badges...")
    from .analytics import calculate_badges
    user_badges = calculate_badges(analytics.user_stats)

    # Set up Jinja2 environment
    template_dir = get_template_dir()
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=False,  # We're handling HTML ourselves
    )
    template = env.get_template("report.html")

    # Format peak hour data
    from .analytics import format_hour, get_hour_emoji
    formatted_hour = format_hour(analytics.most_active_hour)
    hour_emoji = get_hour_emoji(analytics.most_active_hour)

    # Render template
    if not quiet:
        print("[*] Rendering HTML report...")
    html_content = template.render(
        metadata=metadata,
        analytics=analytics,
        charts=charts_html,
        user_sparklines=user_sparklines,
        user_hourly_sparklines=user_hourly_sparklines,
        user_badges=user_badges,
        generation_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        formatted_hour=formatted_hour,
        hour_emoji=hour_emoji,
    )

    # Determine output path
    if output_path is None:
        # Default to current working directory
        if report_name:
            stem = report_name.replace(" ", "_")
        else:
            stem = chat_file.stem.replace(" ", "_")
        output_path = Path.cwd() / f"{stem}_report.html"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write HTML file
    output_path.write_text(html_content, encoding="utf-8")
    if not quiet:
        print(f"[+] HTML report saved: {output_path}")

    return output_path


def generate_pdf_report(
    html_path: str | Path,
    output_path: str | Path | None = None,
    quiet: bool = False,
) -> Path:
    """
    Generate a PDF report from an existing HTML report using Playwright.

    Uses a real Chromium browser to render the HTML, ensuring all CSS
    and JavaScript (including Plotly charts) render correctly.

    Args:
        html_path: Path to the HTML report
        output_path: Path for the output PDF file (optional)
        quiet: Suppress progress messages

    Returns:
        Path to the generated PDF file
    """
    import asyncio

    async def _generate_pdf() -> Path:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            print("[!] Playwright not installed. Install with: uv add playwright")
            print("[!] Then run: playwright install chromium")
            raise

        html_path_resolved = Path(html_path).resolve()

        if not html_path_resolved.exists():
            raise FileNotFoundError(f"HTML file not found: {html_path_resolved}")

        # Determine output path
        nonlocal output_path
        if output_path is None:
            output_path = html_path_resolved.with_suffix(".pdf")
        else:
            output_path = Path(output_path).resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)

        if not quiet:
            print("[*] Converting HTML to PDF with Playwright...")

        async with async_playwright() as p:
            # Launch headless Chromium
            browser = await p.chromium.launch()

            # Use a wider viewport for better layout
            # device_scale_factor=2 for high-DPI/retina quality rendering
            page = await browser.new_page(
                viewport={"width": 1400, "height": 800},
                device_scale_factor=2,
            )

            # Navigate to the HTML file
            file_url = html_path_resolved.as_uri()
            await page.goto(file_url)

            # Wait for the page to fully load (including Plotly charts)
            await page.wait_for_load_state("networkidle")

            # Inject CSS to add padding inside the dark background
            await page.add_style_tag(
                content="""
                body {
                    padding: 40px 60px !important;
                }
                .container {
                    max-width: 1200px !important;
                    margin: 0 auto !important;
                }
            """
            )

            # Give Plotly a moment to finish rendering animations
            await page.wait_for_timeout(1000)

            # Measure the full page height for single-page PDF
            page_height = await page.evaluate("document.documentElement.scrollHeight")

            # Generate PDF as a single long page (no margins - padding is in the HTML)
            await page.pdf(
                path=str(output_path),
                width="1400px",
                height=f"{page_height}px",
                print_background=True,  # Keep dark background
                scale=1,
                margin={
                    "top": "0",
                    "bottom": "0",
                    "left": "0",
                    "right": "0",
                },
            )

            await browser.close()

        if not quiet:
            print(f"[+] PDF report saved: {output_path}")

        return output_path

    # Run the async function
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None:
        # Running inside an existing event loop (e.g., Jupyter)
        import nest_asyncio
        nest_asyncio.apply()

    return asyncio.run(_generate_pdf())


def generate_full_report(
    chat_file: str | Path,
    output_dir: str | Path | None = None,
    year_filter: int | None = None,
    min_messages: int = 2,
    report_name: str | None = None,
    generate_pdf: bool = True,
    fixed_layout: bool = False,
    quiet: bool = False,
) -> tuple[Path, Path | None]:
    """
    Generate HTML and optionally PDF reports from a WhatsApp chat export.

    Args:
        chat_file: Path to the WhatsApp export (.zip or .txt)
        output_dir: Directory for output files (optional)
        year_filter: Filter messages to a specific year (optional)
        min_messages: Minimum messages per user to include
        report_name: Custom name for the report file (optional, defaults to chat filename)
        generate_pdf: Whether to also generate PDF
        fixed_layout: Force desktop layout on all devices
        quiet: Suppress progress messages

    Returns:
        Tuple of (html_path, pdf_path or None)
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
    charts_html = chart_collection.to_html_dict(include_plotlyjs_first=True)  # top_users loads Plotly
    
    # Generate user sparklines
    if not quiet:
        print("[*] Generating user sparklines...")
    from .charts import create_user_sparkline, create_user_hourly_sparkline, chart_to_html
    user_sparklines = {}
    user_hourly_sparklines = {}
    for user_stat in analytics.user_stats:
        # Yearly activity sparkline - Plotly already loaded by top_users chart
        sparkline_fig = create_user_sparkline(user_stat.daily_activity, user_stat.name)
        user_sparklines[user_stat.name] = chart_to_html(sparkline_fig, include_plotlyjs=False)
        
        # Hourly pattern sparkline
        hourly_sparkline_fig = create_user_hourly_sparkline(user_stat.hourly_activity, user_stat.name)
        user_hourly_sparklines[user_stat.name] = chart_to_html(hourly_sparkline_fig, include_plotlyjs=False)

    # Calculate user badges
    if not quiet:
        print("[*] Calculating achievement badges...")
    from .analytics import calculate_badges
    user_badges = calculate_badges(analytics.user_stats)

    # Set up Jinja2 environment
    template_dir = get_template_dir()
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=False,
    )
    template = env.get_template("report.html")

    # Determine output paths
    if output_dir is None:
        # Default to current working directory
        output_dir = Path.cwd()
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    if report_name:
        stem = report_name.replace(" ", "_")
    else:
        stem = chat_file.stem.replace(" ", "_")
    html_path = output_dir / f"{stem}_report.html"
    pdf_path = output_dir / f"{stem}_report.pdf" if generate_pdf else None

    # Format peak hour data
    from .analytics import format_hour, get_hour_emoji
    formatted_hour = format_hour(analytics.most_active_hour)
    hour_emoji = get_hour_emoji(analytics.most_active_hour)

    # Render HTML template
    if not quiet:
        print("[*] Rendering HTML report...")
    html_content = template.render(
        metadata=metadata,
        analytics=analytics,
        charts=charts_html,
        user_sparklines=user_sparklines,
        user_hourly_sparklines=user_hourly_sparklines,
        user_badges=user_badges,
        generation_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        fixed_layout=fixed_layout,
        formatted_hour=formatted_hour,
        hour_emoji=hour_emoji,
    )

    # Write HTML file
    html_path.write_text(html_content, encoding="utf-8")
    if not quiet:
        print(f"[+] HTML report saved: {html_path}")

    # Generate PDF if requested
    if generate_pdf and pdf_path:
        try:
            generate_pdf_report(html_path, pdf_path, quiet=quiet)
        except ImportError:
            if not quiet:
                print("[!] Skipping PDF generation (Playwright not available)")
                print("[!] Install with: uv add playwright && playwright install chromium")
            pdf_path = None
        except Exception as e:
            if not quiet:
                print(f"[!] PDF generation failed: {e}")
            pdf_path = None

    return html_path, pdf_path


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
  whatsapp-wrapped chat.zip --pdf --year 2024
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
        "--pdf",
        action="store_true",
        help="Also generate PDF report",
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
        html_path, pdf_path = generate_full_report(
            chat_file=chat_file,
            output_dir=args.output,
            year_filter=args.year,
            min_messages=args.min_messages,
            report_name=args.name,
            generate_pdf=args.pdf,
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
            if pdf_path:
                print(f"  PDF:  {pdf_path}")
            print()

    except Exception as e:
        print(f"\n[!] Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
