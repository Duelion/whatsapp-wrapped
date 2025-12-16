"""
Basic tests for WhatsApp chat parser.
"""

from datetime import datetime

from src.parser import (
    _detect_date_order,
    _parse_timestamp,
    filter_bot_users,
    parse_chat,
    parse_whatsapp_export,
)


def test_parse_chat_file(chat_file_path, full_chat_data):
    """Test that chat file can be parsed."""
    df, metadata = full_chat_data
    assert len(df) > 0
    assert metadata.total_messages > 0


def test_dataframe_has_required_columns(chat_data_3months):
    """Test DataFrame has expected columns."""
    df, _ = chat_data_3months
    assert "timestamp" in df.columns
    assert "name" in df.columns
    assert "message" in df.columns
    assert "message_type" in df.columns


def test_three_month_filter(chat_data_3months, full_chat_data):
    """Test 3-month filtering reduces dataset."""
    df_filtered, _ = chat_data_3months
    df_full, _ = full_chat_data
    assert len(df_filtered) < len(df_full)


def test_pandas_operations(chat_data_3months):
    """Test basic pandas operations work."""
    df, _ = chat_data_3months

    # Basic operations
    assert df["name"].nunique() > 0
    assert df["message_type"].value_counts()["text"] > 0
    assert df["timestamp"].dtype == "datetime64[ns]"

    # DateTime operations
    assert df["timestamp"].dt.year.nunique() > 0
    assert df["timestamp"].dt.hour.nunique() > 0

    # GroupBy operations
    user_counts = df.groupby("name").size()
    assert len(user_counts) > 0


def test_message_type_classification(full_chat_data):
    """Test that message types are properly classified."""
    df, _ = full_chat_data

    # Check that message_type column exists and has valid values
    assert "message_type" in df.columns
    message_types = df["message_type"].unique()

    # Should have at least 'text' type
    assert "text" in message_types

    # Check that other types can exist
    valid_types = [
        "text",
        "image",
        "video",
        "audio",
        "sticker",
        "gif",
        "link",
        "document",
        "contact",
        "location",
    ]
    for msg_type in message_types:
        assert msg_type in valid_types


def test_system_message_filtering(chat_file_path):
    """Test that system messages are filtered out."""
    # Parse without filtering
    df_unfiltered, _ = parse_whatsapp_export(chat_file_path, filter_system=False)

    # Parse with filtering
    df_filtered, _ = parse_whatsapp_export(chat_file_path, filter_system=True)

    # Filtered should have same or fewer messages
    assert len(df_filtered) <= len(df_unfiltered)

    # Check that common system message patterns are not in filtered data
    system_keywords = ["added", "removed", "left", "changed the subject", "created group"]
    for keyword in system_keywords:
        matches = df_filtered["message"].str.contains(keyword, case=False, na=False).sum()
        # Should have very few or no system messages
        assert matches < len(df_filtered) * 0.1  # Less than 10% should contain these keywords


def test_bot_user_filtering(chat_file_path):
    """Test that bot users like Meta AI are filtered out."""
    from src.parser import load_chat_file, parse_chat

    # Load and parse without bot filtering
    raw_text = load_chat_file(chat_file_path)
    df = parse_chat(raw_text)

    # Apply bot filter
    df_filtered = filter_bot_users(df)

    # Check that Meta AI is not in filtered data
    assert "Meta AI" not in df_filtered["name"].values
    assert "meta ai" not in df_filtered["name"].str.lower().values


def test_year_filter(chat_file_path):
    """Test that year filtering works correctly."""
    # Get all data first
    df_full, _ = parse_whatsapp_export(chat_file_path, filter_system=True)

    # Get available years
    years = df_full["timestamp"].dt.year.unique()

    if len(years) > 1:
        # Pick the first year
        test_year = int(years[0])

        # Parse with year filter
        df_year, _ = parse_whatsapp_export(
            chat_file_path, filter_system=True, year_filter=test_year
        )

        # All messages should be from the specified year
        assert (df_year["timestamp"].dt.year == test_year).all()

        # Should be fewer messages than full dataset
        assert len(df_year) < len(df_full)


def test_min_messages_filter(chat_file_path):
    """Test that min_messages filter removes low-activity users."""
    # Parse with low threshold
    df_low, metadata_low = parse_whatsapp_export(chat_file_path, filter_system=True, min_messages=2)

    # Parse with higher threshold
    df_high, metadata_high = parse_whatsapp_export(
        chat_file_path, filter_system=True, min_messages=50
    )

    # Higher threshold should have fewer or equal members
    assert metadata_high.total_members <= metadata_low.total_members

    # Verify all users in high threshold have at least min_messages
    if len(df_high) > 0:
        user_counts = df_high["name"].value_counts()
        assert (user_counts >= 50).all()


def test_metadata_accuracy(chat_file_path):
    """Test that metadata accurately reflects the parsed data."""
    df, metadata = parse_whatsapp_export(chat_file_path, filter_system=True)

    # Check metadata matches DataFrame
    assert metadata.total_messages == len(df)
    assert metadata.total_members == df["name"].nunique()
    assert metadata.date_range_start == df["timestamp"].min()
    assert metadata.date_range_end == df["timestamp"].max()
    assert len(metadata.member_names) == metadata.total_members

    # Check member names match
    assert set(metadata.member_names) == set(df["name"].unique())


def test_timestamp_parsing_and_sorting(full_chat_data):
    """Test that timestamps are correctly parsed and sorted."""
    df, _ = full_chat_data

    # Check timestamp is datetime type
    assert df["timestamp"].dtype == "datetime64[ns]"

    # Check timestamps are sorted (allowing for potential ties)
    timestamps = df["timestamp"].values
    assert all(timestamps[i] <= timestamps[i + 1] for i in range(len(timestamps) - 1))

    # Check no null timestamps
    assert df["timestamp"].notna().all()


def test_link_detection_in_messages(full_chat_data):
    """Test that links in messages are properly detected."""
    df, _ = full_chat_data

    # Find messages classified as links
    link_messages = df[df["message_type"] == "link"]

    if len(link_messages) > 0:
        # Check that link messages contain http:// or https://
        for msg in link_messages["message"].head(10):
            assert "http://" in msg.lower() or "https://" in msg.lower()


# ==== NEW TESTS FOR FORMAT IMPROVEMENTS ====


def test_am_pm_time_parsing():
    """Test that 12-hour AM/PM timestamps are correctly parsed."""
    # Test various AM/PM formats
    test_cases = [
        ("12/25/23, 3:45 PM", True),
        ("12/25/23, 3:45:30 PM", True),
        ("25/12/23, 11:30 AM", True),
        ("25/12/23, 11:30:45 AM", True),
        # Test no-space variants (should be normalized)
        ("12/25/23, 3:45PM", True),
        ("12/25/23, 11:30am", True),
    ]

    for timestamp_str, should_parse in test_cases:
        result = _parse_timestamp(timestamp_str)
        if should_parse:
            assert result is not None, f"Failed to parse: {timestamp_str}"
            assert isinstance(result, datetime)
        else:
            assert result is None, f"Should not have parsed: {timestamp_str}"


def test_unicode_direction_marks():
    """Test that Unicode direction marks don't break parsing."""
    # Sample chat with LRM (Left-to-Right Mark)
    chat_with_lrm = """\u200e12/25/23, 10:30 - Alice: Hello
\u200e12/25/23, 10:31 - Bob: Hi there"""

    df = parse_chat(chat_with_lrm)

    # Should parse both messages
    assert len(df) == 2
    assert df.iloc[0]["name"] == "Alice"
    assert df.iloc[1]["name"] == "Bob"


def test_date_order_detection_dd_mm():
    """Test detection of DD/MM date format."""
    # Chat with dates that clearly show DD/MM (day > 12)
    chat_dd_mm = """25/12/23, 10:30 - Alice: Merry Christmas
31/01/23, 15:45 - Bob: Happy New Year"""

    date_order = _detect_date_order(chat_dd_mm)
    assert date_order == "DD/MM"


def test_date_order_detection_mm_dd():
    """Test detection of MM/DD date format."""
    # Chat with dates that clearly show MM/DD (second component > 12)
    chat_mm_dd = """12/25/23, 10:30 - Alice: Merry Christmas
01/31/23, 15:45 - Bob: Happy New Year"""

    date_order = _detect_date_order(chat_mm_dd)
    assert date_order == "MM/DD"


def test_date_order_detection_ambiguous():
    """Test that ambiguous dates are detected as such."""
    # Chat with only ambiguous dates (both components <= 12)
    chat_ambiguous = """05/10/23, 10:30 - Alice: Hello
03/04/23, 15:45 - Bob: Hi"""

    date_order = _detect_date_order(chat_ambiguous)
    assert date_order == "ambiguous"


def test_system_messages_without_author():
    """Test that system messages without author are parsed."""
    # Android-style system message
    chat_android_system = """12/25/23, 10:30 - Messages and calls are end-to-end encrypted
12/25/23, 10:31 - Alice: Hello"""

    df = parse_chat(chat_android_system)

    # Should parse both messages
    assert len(df) >= 1  # At least the user message
    assert "Alice" in df["name"].values

    # Check if system message was captured
    system_messages = df[df["name"] == "System"]
    if len(system_messages) > 0:
        assert "encrypted" in system_messages.iloc[0]["message"].lower()


def test_ios_bracketed_format():
    """Test parsing of iOS bracketed timestamp format."""
    chat_ios = """[12/25/23, 10:30:45] Alice: Hello
[12/25/23, 10:31:20] Bob: Hi there"""

    df = parse_chat(chat_ios)

    assert len(df) == 2
    assert df.iloc[0]["name"] == "Alice"
    assert df.iloc[1]["name"] == "Bob"


def test_multiline_message_parsing():
    """Test that messages spanning multiple lines are correctly parsed."""
    chat_multiline = """12/25/23, 10:30 - Alice: This is a long message
that spans multiple
lines
12/25/23, 10:31 - Bob: Short message"""

    df = parse_chat(chat_multiline)

    assert len(df) == 2
    # Alice's message should contain newlines
    assert "\n" in df.iloc[0]["message"]
    assert "multiple" in df.iloc[0]["message"]
    assert "lines" in df.iloc[0]["message"]
    # Bob's message should be single line
    assert df.iloc[1]["message"] == "Short message"


def test_mixed_format_handling():
    """Test parsing of chat with mixed 12/24 hour times."""
    chat_mixed = """12/25/23, 10:30 AM - Alice: Morning
12/25/23, 15:45 - Bob: Afternoon"""

    df = parse_chat(chat_mixed)

    # Should parse both messages correctly
    assert len(df) == 2
    assert df.iloc[0]["timestamp"].hour == 10
    assert df.iloc[1]["timestamp"].hour == 15


def test_media_placeholder_detection():
    """Test that media placeholders are properly classified."""
    chat_with_media = """12/25/23, 10:30 - Alice: <Media omitted>
12/25/23, 10:31 - Bob: image omitted
12/25/23, 10:32 - Alice: Regular message"""

    df = parse_chat(chat_with_media)

    assert len(df) == 3
    # First two should be media types
    assert df.iloc[0]["message_type"] in ["image", "video", "audio", "sticker"]
    # Third should be text
    assert df.iloc[2]["message_type"] == "text"


def test_empty_message_handling():
    """Test that empty messages don't crash the parser."""
    chat_with_empty = """12/25/23, 10:30 - Alice:
12/25/23, 10:31 - Bob: Not empty"""

    df = parse_chat(chat_with_empty)

    # Should handle empty message gracefully
    assert len(df) == 2
    assert df.iloc[0]["message"] == ""
    assert df.iloc[1]["message"] == "Not empty"


def test_special_characters_in_names():
    """Test that special characters in names are handled."""
    chat_special = """12/25/23, 10:30 - Alice 🎄: Merry Christmas
12/25/23, 10:31 - Bob (Work): Hi"""

    df = parse_chat(chat_special)

    # Should parse both messages
    assert len(df) == 2
    # Names should be captured (even if cleaned later)
    assert len(df.iloc[0]["name"]) > 0
    assert len(df.iloc[1]["name"]) > 0
