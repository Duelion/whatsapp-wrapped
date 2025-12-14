"""
Pytest configuration and fixtures for WhatsApp Wrapped tests.
"""

import sys
from datetime import timedelta
from pathlib import Path

import pytest

from src.parser import parse_whatsapp_export

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


@pytest.fixture(scope="session")
def chat_file_path():
    """Return the path to the WhatsApp chat export file."""
    # Use the test data file in tests/data directory
    test_data_dir = Path(__file__).parent / "data"
    
    # Look for .zip files first, then .txt files
    chat_files = list(test_data_dir.glob("*.zip"))
    if not chat_files:
        chat_files = list(test_data_dir.glob("*.txt"))
    
    if not chat_files:
        pytest.skip("No WhatsApp chat export file (.zip or .txt) found in tests/data/ for testing")
    
    # Use the first file found (there should only be one)
    return chat_files[0]


@pytest.fixture(scope="session")
def full_chat_data(chat_file_path):
    """Parse the full WhatsApp chat export (session-scoped for performance)."""
    df, metadata = parse_whatsapp_export(chat_file_path, filter_system=True)
    return df, metadata


@pytest.fixture(scope="session")
def chat_data_3months(full_chat_data):
    """Filter to last 3 months for faster tests."""
    df, metadata = full_chat_data
    end_date = df["timestamp"].max()
    start_date = end_date - timedelta(days=90)
    df_filtered = df[df["timestamp"] >= start_date].copy()
    return df_filtered, metadata
