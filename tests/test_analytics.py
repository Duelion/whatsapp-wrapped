"""
Integration tests for analytics module.
"""

from src.analytics import analyze_chat, calculate_user_stats


def test_analyze_chat_returns_valid_structure(chat_data_3months):
    """Test that analyze_chat returns ChatAnalytics with all expected fields."""
    df, _ = chat_data_3months
    
    analytics = analyze_chat(df)
    
    # Check overview stats exist and are valid
    assert analytics.total_messages > 0
    assert analytics.total_members > 0
    assert analytics.total_days > 0
    assert analytics.messages_per_day > 0
    assert isinstance(analytics.most_active_day, str)
    assert 0 <= analytics.most_active_hour <= 23
    
    # Check user stats
    assert len(analytics.user_stats) > 0
    assert len(analytics.user_stats) == analytics.total_members
    assert len(analytics.top_messagers) > 0
    
    # Verify user_stats are sorted by message count
    message_counts = [u.total_messages for u in analytics.user_stats]
    assert message_counts == sorted(message_counts, reverse=True)
    
    # Check time-based data exists
    assert len(analytics.messages_by_hour) == 24
    assert len(analytics.messages_by_weekday) == 7
    assert len(analytics.messages_by_date) > 0
    assert len(analytics.messages_by_month) > 0
    
    # Check hourly activity heatmap data
    assert analytics.hourly_activity_by_user.shape[1] == 24  # 24 hours
    assert analytics.hourly_activity_by_user.shape[0] > 0  # At least one user
    
    # Check message type data
    assert len(analytics.message_type_counts) > 0
    assert "text" in analytics.message_type_counts.index
    
    # Check emoji stats
    assert isinstance(analytics.emoji_diversity, int)
    assert analytics.emoji_diversity >= 0
    assert isinstance(analytics.top_emojis_overall, list)
    
    # Check special stats
    assert isinstance(analytics.busiest_day, tuple)
    assert len(analytics.busiest_day) == 2
    assert isinstance(analytics.quietest_day, tuple)
    assert len(analytics.quietest_day) == 2
    assert isinstance(analytics.longest_conversation, dict)
    assert "date" in analytics.longest_conversation
    assert "messages" in analytics.longest_conversation
    assert "participants" in analytics.longest_conversation


def test_user_stats_structure(chat_data_3months):
    """Test that UserStats have all expected fields populated."""
    df, _ = chat_data_3months
    
    # Get a user with reasonable activity
    user_counts = df["name"].value_counts()
    test_user = user_counts.index[0]  # Most active user
    
    # Calculate stats for the user
    date_range = df["timestamp"].dt.date.unique()
    user_stats = calculate_user_stats(df, test_user, date_range)
    
    # Check all fields exist and are valid
    assert user_stats.name == test_user
    assert user_stats.total_messages > 0
    assert user_stats.total_words >= 0
    assert user_stats.avg_message_length >= 0
    assert isinstance(user_stats.top_emojis, list)
    assert user_stats.emoji_count >= 0
    assert user_stats.longest_silence_days >= 0
    assert user_stats.longest_streak_days > 0
    assert 0 <= user_stats.most_active_hour <= 23
    assert isinstance(user_stats.message_types, dict)
    assert user_stats.activity_category in ["night_owl", "early_bird", "balanced"]
    
    # Check activity series
    assert len(user_stats.daily_activity) > 0
    assert len(user_stats.hourly_activity) == 24


def test_emoji_extraction(chat_data_3months):
    """Test that emoji extraction works on actual messages."""
    df, _ = chat_data_3months
    analytics = analyze_chat(df)
    
    # If there are emojis in the data, check they were extracted
    if analytics.emoji_diversity > 0:
        assert len(analytics.top_emojis_overall) > 0
        
        # Check emoji format (should be tuples of emoji and count)
        for emoji, count in analytics.top_emojis_overall[:3]:
            assert isinstance(emoji, str)
            assert isinstance(count, int)
            assert count > 0


def test_activity_category_classification(chat_data_3months):
    """Test that users are classified into activity categories."""
    df, _ = chat_data_3months
    analytics = analyze_chat(df)
    
    # Check that all users have valid activity categories
    categories = [u.activity_category for u in analytics.user_stats]
    valid_categories = ["night_owl", "early_bird", "balanced"]
    
    for category in categories:
        assert category in valid_categories
    
    # At least one user should have a category assigned
    assert len(set(categories)) >= 1


def test_message_type_breakdown_by_user(chat_data_3months):
    """Test that message types are tracked per user."""
    df, _ = chat_data_3months
    analytics = analyze_chat(df)
    
    # Check message_type_by_user DataFrame
    assert analytics.message_type_by_user.shape[0] > 0  # At least one user
    assert analytics.message_type_by_user.shape[1] > 0  # At least one message type
    
    # Each user should have at least some text messages
    for user_stats in analytics.user_stats:
        assert "text" in user_stats.message_types
        assert user_stats.message_types["text"] > 0


def test_time_patterns(chat_data_3months):
    """Test that time-based patterns are correctly aggregated."""
    df, _ = chat_data_3months
    analytics = analyze_chat(df)
    
    # Check hourly pattern sums to total messages
    assert analytics.messages_by_hour.sum() == analytics.total_messages
    
    # Check weekday pattern sums to total messages
    assert analytics.messages_by_weekday.sum() == analytics.total_messages
    
    # Check daily pattern sums to total messages
    assert analytics.messages_by_date.sum() == analytics.total_messages
    
    # Most active hour should have the highest count
    max_hour_count = analytics.messages_by_hour.max()
    assert analytics.messages_by_hour[analytics.most_active_hour] == max_hour_count
    
    # Most active day should have the highest count
    max_day_count = analytics.messages_by_weekday.max()
    assert analytics.messages_by_weekday[analytics.most_active_day] == max_day_count


def test_busiest_and_quietest_days(chat_data_3months):
    """Test that busiest and quietest day statistics are valid."""
    df, _ = chat_data_3months
    analytics = analyze_chat(df)
    
    # Busiest day should have more messages than quietest day
    busiest_count = analytics.busiest_day[1]
    quietest_count = analytics.quietest_day[1]
    
    assert busiest_count > 0
    assert quietest_count > 0
    assert busiest_count >= quietest_count
    
    # Date strings should be valid
    assert len(analytics.busiest_day[0]) > 0
    assert len(analytics.quietest_day[0]) > 0


def test_longest_conversation_stats(chat_data_3months):
    """Test that longest conversation statistics are computed."""
    df, _ = chat_data_3months
    analytics = analyze_chat(df)
    
    # Check longest conversation has all required fields
    assert "date" in analytics.longest_conversation
    assert "messages" in analytics.longest_conversation
    assert "participants" in analytics.longest_conversation
    
    # Values should be reasonable
    assert analytics.longest_conversation["messages"] > 0
    assert analytics.longest_conversation["participants"] > 0
    assert analytics.longest_conversation["participants"] <= analytics.total_members







