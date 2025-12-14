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
    # Look for any .zip file in the project root
    project_root = Path(__file__).parent.parent
    chat_files = list(project_root.glob("*.zip"))
    
    if not chat_files:
        pytest.skip("No WhatsApp chat export file (.zip) found in project root for testing")
    
    # Use the first .zip file found
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
