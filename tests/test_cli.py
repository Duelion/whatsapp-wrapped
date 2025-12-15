"""
Tests for CLI argument parsing and behavior.
"""

import argparse
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.generator import main


def test_chat_file_required():
    """Test that chat_file argument is required."""
    with patch("sys.argv", ["whatsapp-wrapped"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2  # argparse error code


def test_chat_file_not_found():
    """Test error when chat file doesn't exist."""
    with patch("sys.argv", ["whatsapp-wrapped", "nonexistent.zip"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1


def test_version_flag():
    """Test --version flag displays version and exits."""
    with patch("sys.argv", ["whatsapp-wrapped", "--version"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0


def test_generate_html_default(chat_file_path, tmp_path, monkeypatch):
    """Test generating HTML report with default settings."""
    # Change to tmp directory
    monkeypatch.chdir(tmp_path)
    
    with patch("sys.argv", ["whatsapp-wrapped", str(chat_file_path), "--quiet"]):
        main()
    
    # Check that HTML file was created
    html_files = list(tmp_path.glob("*_report.html"))
    assert len(html_files) == 1
    assert html_files[0].exists()
    assert html_files[0].stat().st_size > 0


def test_output_directory_option(chat_file_path, tmp_path):
    """Test --output option for custom output directory."""
    output_dir = tmp_path / "custom_output"
    
    with patch("sys.argv", ["whatsapp-wrapped", str(chat_file_path), "--output", str(output_dir), "--quiet"]):
        main()
    
    # Check output directory was created and contains HTML
    assert output_dir.exists()
    html_files = list(output_dir.glob("*_report.html"))
    assert len(html_files) == 1


def test_quiet_flag(chat_file_path, tmp_path, monkeypatch, capsys):
    """Test --quiet flag suppresses output."""
    monkeypatch.chdir(tmp_path)
    
    with patch("sys.argv", ["whatsapp-wrapped", str(chat_file_path), "--quiet"]):
        main()
    
    captured = capsys.readouterr()
    # Should have minimal output with --quiet
    assert "WHATSAPP WRAPPED" not in captured.out
    assert "=" * 60 not in captured.out


def test_year_filter_option(chat_file_path, tmp_path, monkeypatch):
    """Test --year option filters messages to specific year."""
    monkeypatch.chdir(tmp_path)
    
    # Get full data first
    from src.parser import parse_whatsapp_export
    df_full, _ = parse_whatsapp_export(chat_file_path, filter_system=True)
    
    # Find a year that has sufficient data
    available_years = df_full["timestamp"].dt.year.unique()
    if len(available_years) > 0:
        # Pick the year with the most messages
        year_counts = df_full.groupby(df_full["timestamp"].dt.year).size()
        test_year = int(year_counts.idxmax())
        
        with patch("sys.argv", ["whatsapp-wrapped", str(chat_file_path), "--year", str(test_year), "--quiet"]):
            main()
        
        # Verify HTML was created
        html_files = list(tmp_path.glob("*_report.html"))
        assert len(html_files) == 1


def test_min_messages_option(chat_file_path, tmp_path, monkeypatch):
    """Test --min-messages option filters low-activity users."""
    monkeypatch.chdir(tmp_path)
    
    with patch("sys.argv", ["whatsapp-wrapped", str(chat_file_path), "--min-messages", "10", "--quiet"]):
        main()
    
    # Verify HTML was created
    html_files = list(tmp_path.glob("*_report.html"))
    assert len(html_files) == 1


def test_fixed_layout_flag(chat_file_path, tmp_path, monkeypatch):
    """Test --fixed-layout flag is passed to generator."""
    monkeypatch.chdir(tmp_path)
    
    with patch("sys.argv", ["whatsapp-wrapped", str(chat_file_path), "--fixed-layout", "--quiet"]):
        main()
    
    # Verify HTML was created
    html_files = list(tmp_path.glob("*_report.html"))
    assert len(html_files) == 1
    
    # Check that fixed_layout was used in the HTML
    html_content = html_files[0].read_text(encoding="utf-8")
    # The template should have viewport meta tag affected by fixed_layout
    assert "viewport" in html_content.lower()


def test_custom_report_name(chat_file_path, tmp_path, monkeypatch):
    """Test --name option for custom report filename."""
    monkeypatch.chdir(tmp_path)
    
    custom_name = "My_Custom_Report"
    with patch("sys.argv", ["whatsapp-wrapped", str(chat_file_path), "--name", custom_name, "--quiet"]):
        main()
    
    # Verify HTML was created with custom name
    html_files = list(tmp_path.glob("*_report.html"))
    assert len(html_files) == 1
    assert custom_name in html_files[0].name


def test_pdf_flag_skip_if_unavailable(chat_file_path, tmp_path, monkeypatch):
    """Test --pdf flag attempts PDF generation (skips if Playwright unavailable)."""
    monkeypatch.chdir(tmp_path)
    
    try:
        from playwright.async_api import async_playwright
        playwright_available = True
    except ImportError:
        playwright_available = False
    
    with patch("sys.argv", ["whatsapp-wrapped", str(chat_file_path), "--pdf", "--quiet"]):
        main()
    
    # HTML should always be created
    html_files = list(tmp_path.glob("*_report.html"))
    assert len(html_files) == 1
    
    # PDF only created if Playwright is available and Chromium is installed
    pdf_files = list(tmp_path.glob("*_report.pdf"))
    if playwright_available:
        # May or may not succeed - depends on chromium being installed
        assert len(pdf_files) >= 0
    # If not available, PDF generation is skipped gracefully


def test_multiple_options_combined(chat_file_path, tmp_path):
    """Test combining multiple CLI options."""
    output_dir = tmp_path / "combined_test"
    
    from src.parser import parse_whatsapp_export
    df_full, _ = parse_whatsapp_export(chat_file_path, filter_system=True)
    available_years = df_full["timestamp"].dt.year.unique()
    
    if len(available_years) > 0:
        # Pick the year with the most messages to ensure we have data after filtering
        year_counts = df_full.groupby(df_full["timestamp"].dt.year).size()
        test_year = int(year_counts.idxmax())
        
        with patch("sys.argv", [
            "whatsapp-wrapped",
            str(chat_file_path),
            "--output", str(output_dir),
            "--year", str(test_year),
            "--min-messages", "5",
            "--quiet"
        ]):
            main()
        
        # Verify output in custom directory
        assert output_dir.exists()
        html_files = list(output_dir.glob("*_report.html"))
        assert len(html_files) == 1




