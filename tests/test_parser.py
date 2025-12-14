"""
Basic tests for WhatsApp chat parser.
"""

from src.parser import parse_whatsapp_export, filter_system_messages, filter_bot_users


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
    valid_types = ["text", "image", "video", "audio", "sticker", "gif", "link", "document", "contact", "location"]
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
    from src.parser import parse_chat, load_chat_file
    
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
        df_year, _ = parse_whatsapp_export(chat_file_path, filter_system=True, year_filter=test_year)
        
        # All messages should be from the specified year
        assert (df_year["timestamp"].dt.year == test_year).all()
        
        # Should be fewer messages than full dataset
        assert len(df_year) < len(df_full)


def test_min_messages_filter(chat_file_path):
    """Test that min_messages filter removes low-activity users."""
    # Parse with low threshold
    df_low, metadata_low = parse_whatsapp_export(chat_file_path, filter_system=True, min_messages=2)
    
    # Parse with higher threshold
    df_high, metadata_high = parse_whatsapp_export(chat_file_path, filter_system=True, min_messages=50)
    
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
    assert all(timestamps[i] <= timestamps[i+1] for i in range(len(timestamps)-1))
    
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
