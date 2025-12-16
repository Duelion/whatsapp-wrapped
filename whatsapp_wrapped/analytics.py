"""
WhatsApp Chat Analytics Module

Provides comprehensive analysis functions for WhatsApp chat data.
Generates statistics, patterns, and insights for the report.
"""

import contextlib
import math
import re
from dataclasses import dataclass
from datetime import datetime

import pandas as pd
from stop_words import get_stop_words


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
    total_words: int
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
    total_stickers: int  # total stickers sent

    # Word cloud data
    word_frequencies: pd.Series  # Word frequencies for word cloud


def extract_emojis(text: str) -> list[str]:
    """Extract all emojis from a text string using Unicode regex patterns."""
    if pd.isna(text):
        return []

    # Comprehensive emoji regex pattern covering:
    # - Emoticons, symbols, pictographs, transport, maps, flags
    # - Skin tone modifiers, ZWJ sequences, variation selectors
    emoji_pattern = re.compile(
        "["
        "\U0001f600-\U0001f64f"  # Emoticons
        "\U0001f300-\U0001f5ff"  # Misc Symbols and Pictographs
        "\U0001f680-\U0001f6ff"  # Transport and Map
        "\U0001f700-\U0001f77f"  # Alchemical Symbols
        "\U0001f780-\U0001f7ff"  # Geometric Shapes Extended
        "\U0001f800-\U0001f8ff"  # Supplemental Arrows-C
        "\U0001f900-\U0001f9ff"  # Supplemental Symbols and Pictographs
        "\U0001fa00-\U0001fa6f"  # Chess Symbols
        "\U0001fa70-\U0001faff"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027b0"  # Dingbats
        "\U000024c2-\U0001f251"  # Enclosed characters
        "\U0001f1e0-\U0001f1ff"  # Flags (iOS)
        "\U00002600-\U000026ff"  # Misc symbols (sun, moon, etc)
        "\U00002700-\U000027bf"  # Dingbats
        "\U0000fe00-\U0000fe0f"  # Variation Selectors
        "\U0001f000-\U0001f02f"  # Mahjong Tiles
        "\U0001f0a0-\U0001f0ff"  # Playing Cards
        "]+",
        flags=re.UNICODE,
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
                if "\ufe00" <= next_char <= "\ufe0f" or "\U0001f3fb" <= next_char <= "\U0001f3ff":
                    emoji += next_char
                    i += 1
                # Zero Width Joiner sequences
                elif next_char == "\u200d":
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


def extract_word_frequencies(df: pd.DataFrame, min_word_length: int = 3) -> pd.Series:
    """
    Extract word frequencies from all messages for word cloud generation.

    Uses multilingual stopwords and filters out common platform junk.

    Args:
        df: DataFrame with 'message' column
        min_word_length: Minimum word length to include (default: 3)

    Returns:
        pd.Series with words as index and counts as values, sorted descending
    """
    # Build combined stopwords from multiple languages
    languages = [
        "english",
        "spanish",
        "portuguese",
        "french",
        "german",
        "italian",
        "dutch",
        "russian",
        "turkish",
        "arabic",
    ]

    stopwords = set()
    for lang in languages:
        # Skip if language not available
        with contextlib.suppress(Exception):
            stopwords.update(get_stop_words(lang))

    # Add common platform junk and WhatsApp-specific terms
    stopwords.update(
        {
            "rt",
            "https",
            "http",
            "amp",
            "www",
            "com",
            "omitted",
            "media",
            "image",
            "video",
            "audio",
            "sticker",
            "deleted",
            "message",
            "attached",
            "gif",
            "document",
            "edited",
        }
    )

    # Add laughing expressions in multiple languages
    # These often dominate word clouds and aren't meaningful content
    laughing_bases = set()

    # Generate all repeat combinations for common laugh syllables
    # This catches ja, jaja, jajaja... and jaj, jajaj, jajajaj... etc.
    laugh_syllables = [
        # Spanish/Portuguese
        "ja",
        "je",
        "ji",
        "jo",
        "jaj",
        "jej",
        "jij",
        "aja",
        "aje",
        "aji",
        # English
        "ha",
        "he",
        "hi",
        "ho",
        "hah",
        "heh",
        "hih",
        "aha",
        "ahe",
        "ahi",
        # Russian (transliterated)
        "xa",
        "xe",
        "xi",
        "xax",
        "xex",
        "axa",
        # German
        "hö",
        "höh",
        # Portuguese (Brazil)
        "rs",
        # Indonesian
        "wk",
        # Turkish
        "sj",
        "sjs",
        # Generic
        "ah",
        "eh",
        "ih",
        "oh",
        "uh",
    ]

    for base in laugh_syllables:
        for repeat in range(1, 8):
            laughing_bases.add(base * repeat)

    # Single character repeats (k for Brazilian, h for Arabic, etc.)
    for char in ["k", "h", "j", "w", "x", "5"]:
        for i in range(2, 12):
            laughing_bases.add(char * i)

    # Korean (can't repeat easily, add manually)
    laughing_bases.update(["ㅋ" * i for i in range(2, 10)])
    laughing_bases.update(["ㅎ" * i for i in range(2, 10)])

    # Common standalone expressions
    laughing_bases.update(
        [
            # English internet slang
            "lol",
            "lmao",
            "lmfao",
            "rofl",
            "roflmao",
            "lolol",
            "lololol",
            "xd",
            "xdd",
            "xddd",
            "xdddd",
            # French
            "mdr",
            "ptdr",
            "xptdr",
            "mdrr",
            "mdrrr",
            # Keyboard mashing
            "asd",
            "asdf",
            "asdasd",
            "asdas",
            "asdfgh",
            # Thai (5 = "ha" sound)
            "555",
            "5555",
            "55555",
            "555555",
        ]
    )

    stopwords.update(laughing_bases)

    # Unicode-aware regex for letters only (no digits, no punctuation)
    token_re = re.compile(r"[^\W\d_]+", re.UNICODE)

    # Collect all words from text messages only
    all_words = []
    text_messages = df[df["message_type"] == "text"]["message"]

    for msg in text_messages:
        if pd.isna(msg):
            continue
        # Tokenize and filter
        tokens = token_re.findall(str(msg).lower())
        filtered = [t for t in tokens if len(t) >= min_word_length and t not in stopwords]
        all_words.extend(filtered)

    # Create frequency Series using pandas (consistent with emoji frequency code)
    if not all_words:
        return pd.Series(dtype=int)

    word_freq = pd.Series(all_words).value_counts()

    return word_freq


def get_word_count(text: str) -> int:
    """Count words in a message, excluding media placeholders."""
    if pd.isna(text):
        return 0
    # Remove URLs
    text = re.sub(r"https?://\S+", "", str(text))
    # Remove media omitted placeholders
    text = re.sub(r"\w+ omitted", "", text)
    words = text.split()
    return len(words)


def calculate_user_stats(
    df: pd.DataFrame, user_name: str, date_range: pd.DatetimeIndex = None
) -> UserStats:
    """Calculate comprehensive statistics for a single user."""
    user_df = df[df["name"] == user_name].copy()

    # Basic counts
    total_messages = len(user_df)

    # Word count (reuse pre-calculated if available)
    if "word_count" not in user_df.columns:
        user_df["word_count"] = user_df["message"].apply(get_word_count)
    total_words = user_df["word_count"].sum()

    # Average message length (characters)
    text_messages = user_df[user_df["message_type"] == "text"]
    avg_message_length = text_messages["message"].str.len().mean() if len(text_messages) > 0 else 0

    # Emoji analysis (reuse pre-extracted emojis if available)
    if "emojis" in user_df.columns:
        all_emojis = [emoji for emoji_list in user_df["emojis"] for emoji in emoji_list]
    else:
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
    num_days = max(date_range.days, 1)
    messages_per_day = round(total_messages / num_days, 1)

    # Calculate total words and extract emojis once for all messages (performance optimization)
    df["word_count"] = df["message"].apply(get_word_count)
    total_words = int(df["word_count"].sum())
    
    # Extract emojis once for reuse in user stats and overall stats
    df["emojis"] = df["message"].apply(lambda msg: extract_emojis(str(msg)))

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
    full_date_range = pd.date_range(start=min_date, end=max_date, freq="D").date

    # User statistics with normalized date range
    user_names = df["name"].unique()
    user_stats = [calculate_user_stats(df, name, full_date_range) for name in user_names]
    user_stats.sort(key=lambda x: x.total_messages, reverse=True)

    top_messagers = [(u.name, u.total_messages) for u in user_stats]

    # Hourly activity by user (for heatmap)
    hourly_by_user = df.groupby([df["name"], df["timestamp"].dt.hour]).size().unstack(fill_value=0)
    hourly_by_user = hourly_by_user.reindex(columns=range(24), fill_value=0)

    # Message type stats
    message_type_counts = df["message_type"].value_counts()
    message_type_by_user = df.groupby(["name", "message_type"]).size().unstack(fill_value=0)

    # Emoji stats (reuse pre-extracted emojis)
    if "emojis" in df.columns:
        all_emojis = [emoji for emoji_list in df["emojis"] for emoji in emoji_list]
    else:
        all_emojis = []
        for msg in df["message"]:
            all_emojis.extend(extract_emojis(str(msg)))

    emoji_freq = pd.Series(all_emojis).value_counts() if all_emojis else pd.Series(dtype=int)
    top_emojis_overall = list(emoji_freq.head(10).items())
    emoji_diversity = len(emoji_freq)

    # Word frequencies for word cloud
    word_frequencies = extract_word_frequencies(df)

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

    # Format date as human-readable
    formatted_date = datetime.strptime(str(best_day_idx), "%Y-%m-%d").strftime("%B %d, %Y")

    longest_conversation = {
        "date": formatted_date,
        "messages": int(daily_stats.loc[best_day_idx, "messages"]),
        "participants": int(daily_stats.loc[best_day_idx, "participants"]),
    }

    # Total stickers
    total_stickers = int(message_type_counts.get("sticker", 0))

    return ChatAnalytics(
        total_messages=total_messages,
        total_members=total_members,
        total_words=total_words,
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
        total_stickers=total_stickers,
        word_frequencies=word_frequencies,
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


def get_hour_emoji(hour: int) -> str:
    """Get an emoji representing the time of day for a given hour (0-23)."""
    if 0 <= hour < 6:
        return "🌙"  # Night / Late night
    elif 6 <= hour < 12:
        return "🌅"  # Morning / Sunrise
    elif 12 <= hour < 18:
        return "☀️"  # Afternoon / Day
    else:
        return "🌆"  # Evening / Sunset


def get_activity_emoji(category: str) -> str:
    """Get an ASCII art representation for activity category."""
    if category == "night_owl":
        return "🦉"
    elif category == "early_bird":
        return "🐦"
    else:
        return "⚖️"


# Badge definitions for user achievements
BADGE_DEFINITIONS = {
    "streak_master": {
        "emoji": "🔥",
        "label": "Streak Master",
        "description": "Longest consecutive days active",
    },
    "ghost": {
        "emoji": "👻",
        "label": "Ghost",
        "description": "Longest silence between messages",
    },
    "night_owl": {
        "emoji": "🦉",
        "label": "Night Owl",
        "description": "Most active during late night hours",
    },
    "early_bird": {
        "emoji": "🐦",
        "label": "Early Bird",
        "description": "Most active in the morning",
    },
    "emoji_king": {
        "emoji": "😂",
        "label": "Emoji King",
        "description": "Most emojis used",
    },
    "shutterbug": {
        "emoji": "📸",
        "label": "Shutterbug",
        "description": "Most images shared",
    },
    "director": {
        "emoji": "🎬",
        "label": "Director",
        "description": "Most videos shared",
    },
    "sticker_maniac": {
        "emoji": "🎭",
        "label": "Sticker Maniac",
        "description": "Most stickers used",
    },
    "voice_actor": {
        "emoji": "🎤",
        "label": "Voice Actor",
        "description": "Most audio messages",
    },
    "link_sharer": {
        "emoji": "🔗",
        "label": "Link Sharer",
        "description": "Most links shared",
    },
    "novelist": {
        "emoji": "📝",
        "label": "Novelist",
        "description": "Longest average message length",
    },
    "speedster": {
        "emoji": "⚡",
        "label": "Speedster",
        "description": "Shortest average message length",
    },
}


def _is_valid_badge_value(val, threshold):
    """Check if value is valid (not None, not NaN, above threshold)."""
    if val is None:
        return False
    if isinstance(val, float) and math.isnan(val):
        return False
    return val > threshold


def _award_max_badge(
    badge_id: str,
    user_stats: list[UserStats],
    badges_by_user: dict[str, list[dict]],
    metric_func,
    detail_func=None,
    min_value=0,
):
    """Award badge to user(s) with maximum value for a metric."""
    values = [(user, metric_func(user)) for user in user_stats]
    # Filter out NaN values and values below threshold
    values = [(user, val) for user, val in values if _is_valid_badge_value(val, min_value)]

    if not values:
        return

    max_value = max(val for _, val in values)
    winners = [user for user, val in values if val == max_value]

    badge_def = BADGE_DEFINITIONS[badge_id]
    for winner in winners:
        detail = detail_func(winner, max_value) if detail_func else f"{max_value}"
        badges_by_user[winner.name].append(
            {
                "badge_id": badge_id,
                "emoji": badge_def["emoji"],
                "label": badge_def["label"],
                "detail": detail,
            }
        )


def _award_min_badge(
    badge_id: str,
    user_stats: list[UserStats],
    badges_by_user: dict[str, list[dict]],
    metric_func,
    detail_func=None,
    threshold=0,
):
    """Award badge to user(s) with minimum value for a metric."""
    values = [(user, metric_func(user)) for user in user_stats]
    # Filter out NaN values and values at or below threshold
    values = [(user, val) for user, val in values if _is_valid_badge_value(val, threshold)]

    if not values:
        return

    min_val = min(val for _, val in values)
    winners = [user for user, val in values if val == min_val]

    badge_def = BADGE_DEFINITIONS[badge_id]
    for winner in winners:
        detail = detail_func(winner, min_val) if detail_func else f"{min_val}"
        badges_by_user[winner.name].append(
            {
                "badge_id": badge_id,
                "emoji": badge_def["emoji"],
                "label": badge_def["label"],
                "detail": detail,
            }
        )


def calculate_badges(user_stats: list[UserStats]) -> dict[str, list[dict]]:
    """
    Calculate achievement badges for users based on their stats.

    Returns a dict mapping username to list of badge dicts with:
    - badge_id: the badge identifier
    - emoji: the badge emoji
    - label: the badge label
    - detail: specific achievement detail

    Args:
        user_stats: List of UserStats objects

    Returns:
        Dict mapping username to list of earned badges
    """
    if not user_stats:
        return {}

    badges_by_user = {user.name: [] for user in user_stats}

    # Streak Master - longest consecutive days active
    _award_max_badge(
        "streak_master",
        user_stats,
        badges_by_user,
        lambda u: u.longest_streak_days,
        lambda u, v: f"{int(v)} consecutive days",
        min_value=0,
    )

    # Ghost - longest silence between messages
    _award_max_badge(
        "ghost",
        user_stats,
        badges_by_user,
        lambda u: u.longest_silence_days,
        lambda u, v: f"{int(v)} days silent",
        min_value=0,
    )

    # Night Owl - highest percentage of messages during night hours (0-6, 18-24)
    def night_percentage(user):
        night_hours = user.hourly_activity[list(range(0, 6)) + list(range(18, 24))].sum()
        total = user.hourly_activity.sum()
        return (night_hours / total * 100) if total > 0 else 0

    _award_max_badge(
        "night_owl",
        user_stats,
        badges_by_user,
        night_percentage,
        lambda u, v: f"{int(v)}% night messages",
        min_value=0,
    )

    # Early Bird - highest percentage of messages during morning hours (6-12)
    def morning_percentage(user):
        morning_hours = user.hourly_activity[list(range(6, 12))].sum()
        total = user.hourly_activity.sum()
        return (morning_hours / total * 100) if total > 0 else 0

    _award_max_badge(
        "early_bird",
        user_stats,
        badges_by_user,
        morning_percentage,
        lambda u, v: f"{int(v)}% morning messages",
        min_value=0,
    )

    # Emoji King - most emojis used
    _award_max_badge(
        "emoji_king",
        user_stats,
        badges_by_user,
        lambda u: u.emoji_count,
        lambda u, v: f"{int(v):,} emojis used",
        min_value=0,
    )

    # Shutterbug - most images shared
    _award_max_badge(
        "shutterbug",
        user_stats,
        badges_by_user,
        lambda u: u.message_types.get("image", 0),
        lambda u, v: f"{int(v):,} images shared",
        min_value=0,
    )

    # Director - most videos shared
    _award_max_badge(
        "director",
        user_stats,
        badges_by_user,
        lambda u: u.message_types.get("video", 0),
        lambda u, v: f"{int(v):,} videos shared",
        min_value=0,
    )

    # Sticker Maniac - most stickers sent
    _award_max_badge(
        "sticker_maniac",
        user_stats,
        badges_by_user,
        lambda u: u.message_types.get("sticker", 0),
        lambda u, v: f"{int(v):,} stickers sent",
        min_value=0,
    )

    # Voice Actor - most audio/voice messages
    _award_max_badge(
        "voice_actor",
        user_stats,
        badges_by_user,
        lambda u: u.message_types.get("audio", 0),
        lambda u, v: f"{int(v):,} voice messages",
        min_value=0,
    )

    # Link Sharer - most links shared
    _award_max_badge(
        "link_sharer",
        user_stats,
        badges_by_user,
        lambda u: u.message_types.get("link", 0),
        lambda u, v: f"{int(v):,} links shared",
        min_value=0,
    )

    # Novelist - longest average message length
    _award_max_badge(
        "novelist",
        user_stats,
        badges_by_user,
        lambda u: u.avg_message_length,
        lambda u, v: f"{int(v)} chars/message",
        min_value=0,
    )

    # Speedster - shortest average message length
    _award_min_badge(
        "speedster",
        user_stats,
        badges_by_user,
        lambda u: u.avg_message_length,
        lambda u, v: f"{int(v)} chars/message",
        threshold=0,
    )

    return badges_by_user
