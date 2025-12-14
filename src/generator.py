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
    quiet: bool = False,
) -> Path:
    """
    Generate an HTML report from a WhatsApp chat export.

    Args:
        chat_file: Path to the WhatsApp export (.zip or .txt)
        output_path: Path for the output HTML file (optional)
        year_filter: Filter messages to a specific year (optional)
        min_messages: Minimum messages per user to include
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
    for user_stat in analytics.user_stats[:12]:  # Top 12 users
        # Yearly activity sparkline - Plotly already loaded by top_users chart
        sparkline_fig = create_user_sparkline(user_stat.daily_activity, user_stat.name)
        user_sparklines[user_stat.name] = chart_to_html(sparkline_fig, include_plotlyjs=False)
        
        # Hourly pattern sparkline
        hourly_sparkline_fig = create_user_hourly_sparkline(user_stat.hourly_activity, user_stat.name)
        user_hourly_sparklines[user_stat.name] = chart_to_html(hourly_sparkline_fig, include_plotlyjs=False)

    # Set up Jinja2 environment
    template_dir = get_template_dir()
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=False,  # We're handling HTML ourselves
    )
    template = env.get_template("report.html")

    # Render template
    if not quiet:
        print("[*] Rendering HTML report...")
    html_content = template.render(
        metadata=metadata,
        analytics=analytics,
        charts=charts_html,
        user_sparklines=user_sparklines,
        user_hourly_sparklines=user_hourly_sparklines,
        chart_images=None,  # No static images for HTML
        generation_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    # Determine output path
    if output_path is None:
        # Default to current working directory
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
    Generate a PDF report from an existing HTML report.

    Args:
        html_path: Path to the HTML report
        output_path: Path for the output PDF file (optional)
        quiet: Suppress progress messages

    Returns:
        Path to the generated PDF file
    """
    try:
        from weasyprint import CSS, HTML
    except ImportError:
        print("[!] WeasyPrint not installed. Install with: uv add weasyprint")
        print("[!] Note: WeasyPrint requires GTK libraries on Windows.")
        raise

    html_path = Path(html_path)

    if not html_path.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")

    if not quiet:
        print("[*] Converting HTML to PDF...")

    # Determine output path
    if output_path is None:
        output_path = html_path.with_suffix(".pdf")
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # Additional CSS for PDF to ensure proper rendering
    pdf_css = CSS(
        string="""
        @page {
            size: A4;
            margin: 1.5cm;
            background-color: #0d1117;
        }

        body {
            font-size: 10pt;
        }

        /* Force static images for PDF */
        .chart-interactive {
            display: none !important;
        }

        .chart-static {
            display: block !important;
        }

        /* Ensure backgrounds print */
        * {
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }
    """
    )

    # Generate PDF
    html_doc = HTML(filename=str(html_path))
    html_doc.write_pdf(str(output_path), stylesheets=[pdf_css])

    if not quiet:
        print(f"[+] PDF report saved: {output_path}")

    return output_path


def generate_full_report(
    chat_file: str | Path,
    output_dir: str | Path | None = None,
    year_filter: int | None = None,
    min_messages: int = 2,
    generate_pdf: bool = True,
    fixed_layout: bool = False,
    quiet: bool = False,
) -> tuple[Path, Path | None]:
    """
    Generate both HTML and PDF reports with static chart images for PDF.

    Args:
        chat_file: Path to the WhatsApp export (.zip or .txt)
        output_dir: Directory for output files (optional)
        year_filter: Filter messages to a specific year (optional)
        min_messages: Minimum messages per user to include
        generate_pdf: Whether to also generate PDF
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
    for user_stat in analytics.user_stats[:12]:  # Top 12 users
        # Yearly activity sparkline - Plotly already loaded by top_users chart
        sparkline_fig = create_user_sparkline(user_stat.daily_activity, user_stat.name)
        user_sparklines[user_stat.name] = chart_to_html(sparkline_fig, include_plotlyjs=False)
        
        # Hourly pattern sparkline
        hourly_sparkline_fig = create_user_hourly_sparkline(user_stat.hourly_activity, user_stat.name)
        user_hourly_sparklines[user_stat.name] = chart_to_html(hourly_sparkline_fig, include_plotlyjs=False)

    # Generate static images for PDF if requested
    chart_images = None
    if generate_pdf:
        if not quiet:
            print("[*] Generating static chart images for PDF...")
        try:
            chart_images = chart_collection.to_png_dict()
            # Check if any images were generated
            if not any(chart_images.values()):
                if not quiet:
                    print("[!] Warning: Could not generate chart images. PDF charts may be missing.")
                    print("[!] Install kaleido: uv add kaleido")
                chart_images = None
        except Exception as e:
            if not quiet:
                print(f"[!] Warning: Could not generate chart images: {e}")
            chart_images = None

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

    stem = chat_file.stem.replace(" ", "_")
    html_path = output_dir / f"{stem}_report.html"
    pdf_path = output_dir / f"{stem}_report.pdf" if generate_pdf else None

    # Render HTML template
    if not quiet:
        print("[*] Rendering HTML report...")
    html_content = template.render(
        metadata=metadata,
        analytics=analytics,
        charts=charts_html,
        user_sparklines=user_sparklines,
        user_hourly_sparklines=user_hourly_sparklines,
        chart_images=chart_images,
        generation_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        fixed_layout=fixed_layout,
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
                print("[!] Skipping PDF generation (WeasyPrint not available)")
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
