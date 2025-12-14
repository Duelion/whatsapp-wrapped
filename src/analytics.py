"""
WhatsApp Chat Analytics Module

Provides comprehensive analysis functions for WhatsApp chat data.
Generates statistics, patterns, and insights for the report.
"""

from dataclasses import dataclass

import pandas as pd


@dataclass
class UserStats:
    """Statistics for a single user."""

    name: str
    total_messages: int
    total_words: int
    avg_message_length: float
    top_emojis: list[tuple[str, int]]  # List of (emoji, count) tuples
    emoji_count: int
    longest_silence_days: int
    longest_streak_days: int
    most_active_hour: int
    message_types: dict[str, int]
    activity_category: str  # "night_owl", "early_bird", "balanced"
    daily_activity: pd.Series  # Daily message counts for sparkline
    hourly_activity: pd.Series  # Hourly message counts (0-23) for daily pattern sparkline


@dataclass
class ChatAnalytics:
    """Complete analytics for a WhatsApp chat."""

    # Overview stats
    total_messages: int
    total_members: int
    total_days: int
    messages_per_day: float
    most_active_day: str
    most_active_hour: int

    # User rankings
    user_stats: list[UserStats]
    top_messagers: list[tuple[str, int]]

    # Time-based data
    messages_by_hour: pd.Series
    messages_by_weekday: pd.Series
    messages_by_date: pd.Series
    messages_by_month: pd.Series

    # Hourly activity per user (for heatmap)
    hourly_activity_by_user: pd.DataFrame

    # Message type breakdown
    message_type_counts: pd.Series
    message_type_by_user: pd.DataFrame

    # Emoji stats
    top_emojis_overall: list[tuple[str, int]]
    emoji_diversity: int  # unique emojis used

    # Special stats
    busiest_day: tuple[str, int]  # (date_str, count)
    quietest_day: tuple[str, int]
    longest_conversation: dict  # day with most back-and-forth


def extract_emojis(text: str) -> list[str]:
    """Extract all emojis from a text string using Unicode regex patterns."""
    import re
    
    if pd.isna(text):
        return []
    
    # Comprehensive emoji regex pattern covering:
    # - Emoticons, symbols, pictographs, transport, maps, flags
    # - Skin tone modifiers, ZWJ sequences, variation selectors
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F300-\U0001F5FF"  # Misc Symbols and Pictographs
        "\U0001F680-\U0001F6FF"  # Transport and Map
        "\U0001F700-\U0001F77F"  # Alchemical Symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"  # Enclosed characters
        "\U0001F1E0-\U0001F1FF"  # Flags (iOS)
        "\U00002600-\U000026FF"  # Misc symbols (sun, moon, etc)
        "\U00002700-\U000027BF"  # Dingbats
        "\U0000FE00-\U0000FE0F"  # Variation Selectors
        "\U0001F000-\U0001F02F"  # Mahjong Tiles
        "\U0001F0A0-\U0001F0FF"  # Playing Cards
        "]+",
        flags=re.UNICODE
    )
    
    # Find all emoji matches
    matches = emoji_pattern.findall(str(text))
    
    # Split compound emojis (like flags or ZWJ sequences) into individual base emojis
    # But keep them together if they form a single visual emoji
    result = []
    for match in matches:
        # Each match could be a sequence of emojis, split them
        # But be careful with ZWJ sequences and skin tones
        i = 0
        while i < len(match):
            char = match[i]
            emoji = char
            # Check for variation selectors or skin tone modifiers following
            while i + 1 < len(match):
                next_char = match[i + 1]
                # Variation selectors (FE0E, FE0F) and skin tone modifiers
                if '\uFE00' <= next_char <= '\uFE0F' or '\U0001F3FB' <= next_char <= '\U0001F3FF':
                    emoji += next_char
                    i += 1
                # Zero Width Joiner sequences
                elif next_char == '\u200D':
                    # Include ZWJ and the next character(s)
                    emoji += next_char
                    i += 1
                    if i + 1 < len(match):
                        emoji += match[i + 1]
                        i += 1
                else:
                    break
            result.append(emoji)
            i += 1
    
    return result


def get_word_count(text: str) -> int:
    """Count words in a message, excluding media placeholders."""
    if pd.isna(text):
        return 0
    # Remove URLs
    text = pd.Series([text]).str.replace(r"https?://\S+", "", regex=True).iloc[0]
    # Remove media omitted placeholders
    text = pd.Series([text]).str.replace(r"\w+ omitted", "", regex=True).iloc[0]
    words = text.split()
    return len(words)


def calculate_user_stats(df: pd.DataFrame, user_name: str, date_range: pd.DatetimeIndex = None) -> UserStats:
    """Calculate comprehensive statistics for a single user."""
    user_df = df[df["name"] == user_name].copy()

    # Basic counts
    total_messages = len(user_df)

    # Word count
    user_df["word_count"] = user_df["message"].apply(get_word_count)
    total_words = user_df["word_count"].sum()

    # Average message length (characters)
    text_messages = user_df[user_df["message_type"] == "text"]
    avg_message_length = text_messages["message"].str.len().mean() if len(text_messages) > 0 else 0

    # Emoji analysis
    all_emojis = []
    for msg in user_df["message"]:
        all_emojis.extend(extract_emojis(str(msg)))

    emoji_count = len(all_emojis)
    emoji_freq = pd.Series(all_emojis).value_counts()
    top_emojis = list(emoji_freq.head(7).items()) if len(emoji_freq) > 0 else []

    # Daily activity for sparkline - normalized to full date range
    daily_activity = user_df.groupby(user_df["timestamp"].dt.date).size()
    
    # If date_range is provided, reindex to fill the entire range with 0s
    if date_range is not None:
        daily_activity = daily_activity.reindex(date_range, fill_value=0)

    # Silence and streak analysis
    (user_df.set_index("timestamp").resample("D").size().reset_index(name="count"))

    # Calculate longest silence (days between messages)
    message_dates = user_df["timestamp"].dt.date.unique()
    if len(message_dates) > 1:
        date_diffs = pd.Series(sorted(message_dates)).diff().dropna()
        longest_silence = date_diffs.max().days if len(date_diffs) > 0 else 0
    else:
        longest_silence = 0

    # Calculate longest streak (consecutive days with messages)
    if len(message_dates) > 1:
        dates_sorted = pd.Series(sorted(message_dates))
        diffs = dates_sorted.diff().dt.days
        streak_groups = (diffs != 1).cumsum()
        streak_lengths = dates_sorted.groupby(streak_groups).size()
        longest_streak = streak_lengths.max()
    else:
        longest_streak = 1 if len(message_dates) == 1 else 0

    # Most active hour
    hour_counts = user_df["timestamp"].dt.hour.value_counts()
    most_active_hour = hour_counts.idxmax() if len(hour_counts) > 0 else 12

    # Hourly activity distribution (0-23)
    hourly_activity = user_df.groupby(user_df["timestamp"].dt.hour).size()
    hourly_activity = hourly_activity.reindex(range(24), fill_value=0)

    # Message type breakdown
    message_types = user_df["message_type"].value_counts().to_dict()

    # Activity category based on hour distribution
    night_hours = user_df["timestamp"].dt.hour.isin(range(0, 6)).sum()
    morning_hours = user_df["timestamp"].dt.hour.isin(range(6, 12)).sum()
    afternoon_hours = user_df["timestamp"].dt.hour.isin(range(12, 18)).sum()
    evening_hours = user_df["timestamp"].dt.hour.isin(range(18, 24)).sum()

    if night_hours + evening_hours > morning_hours + afternoon_hours:
        activity_category = "night_owl"
    elif morning_hours > evening_hours:
        activity_category = "early_bird"
    else:
        activity_category = "balanced"

    return UserStats(
        name=user_name,
        total_messages=total_messages,
        total_words=int(total_words),
        avg_message_length=round(avg_message_length, 1),
        top_emojis=top_emojis,
        emoji_count=emoji_count,
        longest_silence_days=longest_silence,
        longest_streak_days=int(longest_streak),
        most_active_hour=most_active_hour,
        message_types=message_types,
        activity_category=activity_category,
        daily_activity=daily_activity,
        hourly_activity=hourly_activity,
    )


def analyze_chat(df: pd.DataFrame) -> ChatAnalytics:
    """
    Perform comprehensive analysis on a WhatsApp chat DataFrame.

    Args:
        df: Parsed chat DataFrame with columns: timestamp, name, message, message_type

    Returns:
        ChatAnalytics object with all computed statistics
    """
    # Overview stats
    total_messages = len(df)
    total_members = df["name"].nunique()

    date_range = df["timestamp"].max() - df["timestamp"].min()
    total_days = max(date_range.days, 1)
    messages_per_day = round(total_messages / total_days, 1)

    # Time-based aggregations
    messages_by_hour = df.groupby(df["timestamp"].dt.hour).size()
    messages_by_hour = messages_by_hour.reindex(range(24), fill_value=0)

    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    messages_by_weekday = df.groupby(df["timestamp"].dt.dayofweek).size()
    messages_by_weekday.index = messages_by_weekday.index.map(lambda x: weekday_names[x])

    messages_by_date = df.groupby(df["timestamp"].dt.date).size()

    messages_by_month = df.groupby(df["timestamp"].dt.to_period("M")).size()
    messages_by_month.index = messages_by_month.index.astype(str)

    # Most active day/hour
    most_active_day = messages_by_weekday.idxmax()
    most_active_hour = messages_by_hour.idxmax()

    # Create full date range for normalized sparklines
    min_date = df["timestamp"].min().date()
    max_date = df["timestamp"].max().date()
    full_date_range = pd.date_range(start=min_date, end=max_date, freq='D').date

    # User statistics with normalized date range
    user_names = df["name"].unique()
    user_stats = [calculate_user_stats(df, name, full_date_range) for name in user_names]
    user_stats.sort(key=lambda x: x.total_messages, reverse=True)

    top_messagers = [(u.name, u.total_messages) for u in user_stats[:10]]

    # Hourly activity by user (for heatmap)
    hourly_by_user = df.groupby([df["name"], df["timestamp"].dt.hour]).size().unstack(fill_value=0)
    hourly_by_user = hourly_by_user.reindex(columns=range(24), fill_value=0)

    # Message type stats
    message_type_counts = df["message_type"].value_counts()
    message_type_by_user = df.groupby(["name", "message_type"]).size().unstack(fill_value=0)

    # Emoji stats
    all_emojis = []
    for msg in df["message"]:
        all_emojis.extend(extract_emojis(str(msg)))

    emoji_freq = pd.Series(all_emojis).value_counts()
    top_emojis_overall = list(emoji_freq.head(10).items())
    emoji_diversity = len(emoji_freq)

    # Special stats
    busiest_date = messages_by_date.idxmax()
    busiest_day = (str(busiest_date), int(messages_by_date.max()))

    # Filter out days with 0 messages for quietest day
    active_days = messages_by_date[messages_by_date > 0]
    if len(active_days) > 0:
        quietest_date = active_days.idxmin()
        quietest_day = (str(quietest_date), int(active_days.min()))
    else:
        quietest_day = ("N/A", 0)

    # Longest conversation: day with most unique participants and messages
    daily_stats = df.groupby(df["timestamp"].dt.date).agg(
        messages=("message", "count"),
        participants=("name", "nunique"),
    )
    daily_stats["score"] = daily_stats["messages"] * daily_stats["participants"]
    best_day_idx = daily_stats["score"].idxmax()
    longest_conversation = {
        "date": str(best_day_idx),
        "messages": int(daily_stats.loc[best_day_idx, "messages"]),
        "participants": int(daily_stats.loc[best_day_idx, "participants"]),
    }

    return ChatAnalytics(
        total_messages=total_messages,
        total_members=total_members,
        total_days=total_days,
        messages_per_day=messages_per_day,
        most_active_day=most_active_day,
        most_active_hour=most_active_hour,
        user_stats=user_stats,
        top_messagers=top_messagers,
        messages_by_hour=messages_by_hour,
        messages_by_weekday=messages_by_weekday,
        messages_by_date=messages_by_date,
        messages_by_month=messages_by_month,
        hourly_activity_by_user=hourly_by_user,
        message_type_counts=message_type_counts,
        message_type_by_user=message_type_by_user,
        top_emojis_overall=top_emojis_overall,
        emoji_diversity=emoji_diversity,
        busiest_day=busiest_day,
        quietest_day=quietest_day,
        longest_conversation=longest_conversation,
    )


def format_duration(days: int) -> str:
    """Format a duration in days to a human-readable string."""
    if days == 0:
        return "< 1 day"
    elif days == 1:
        return "1 day"
    elif days < 7:
        return f"{days} days"
    elif days < 30:
        weeks = days // 7
        return f"{weeks} week{'s' if weeks > 1 else ''}"
    elif days < 365:
        months = days // 30
        return f"{months} month{'s' if months > 1 else ''}"
    else:
        years = days // 365
        return f"{years} year{'s' if years > 1 else ''}"


def format_hour(hour: int) -> str:
    """Format an hour (0-23) to a readable time string."""
    if hour == 0:
        return "12:00 AM"
    elif hour < 12:
        return f"{hour}:00 AM"
    elif hour == 12:
        return "12:00 PM"
    else:
        return f"{hour - 12}:00 PM"


def get_activity_emoji(category: str) -> str:
    """Get an ASCII art representation for activity category."""
    if category == "night_owl":
        return "🦉"
    elif category == "early_bird":
        return "🐦"
    else:
        return "⚖️"
