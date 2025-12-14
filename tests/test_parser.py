"""
Basic tests for WhatsApp chat parser.
"""


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
