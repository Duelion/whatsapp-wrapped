"""
WhatsApp Chat Analytics Module

Provides comprehensive analysis functions for WhatsApp chat data.
Generates statistics, patterns, and insights for the report.
"""

import contextlib
import math
import re
from dataclasses import dataclass
from datetime import date, datetime

import polars as pl
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
    daily_activity: pl.Series  # Daily message counts for sparkline
    hourly_activity: pl.Series  # Hourly message counts (0-23) for daily pattern sparkline


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

    # Time-based data (stored as DataFrames with keys and counts for compatibility with charts)
    messages_by_hour: pl.DataFrame  # columns: hour, count
    messages_by_weekday: pl.DataFrame  # columns: weekday, count
    messages_by_date: pl.DataFrame  # columns: date, count
    messages_by_month: pl.DataFrame  # columns: month, count

    # Hourly activity per user (for heatmap)
    hourly_activity_by_user: pl.DataFrame

    # Message type breakdown
    message_type_counts: pl.DataFrame  # columns: message_type, count
    message_type_by_user: pl.DataFrame

    # Emoji stats
    top_emojis_overall: list[tuple[str, int]]
    emoji_diversity: int  # unique emojis used

    # Special stats
    busiest_day: tuple[str, int]  # (date_str, count)
    quietest_day: tuple[str, int]
    longest_conversation: dict  # day with most back-and-forth
    total_stickers: int  # total stickers sent

    # Word cloud data
    word_frequencies: pl.DataFrame  # Word frequencies for word cloud (columns: word, count)


def extract_emojis(text: str) -> list[str]:
    """Extract all emojis from a text string using Unicode regex patterns."""
    if text is None:
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


def extract_word_frequencies(df: pl.DataFrame, min_word_length: int = 3) -> pl.DataFrame:
    """
    Extract word frequencies from all messages for word cloud generation.

    Uses multilingual stopwords and filters out common platform junk.

    Args:
        df: DataFrame with 'message' column
        min_word_length: Minimum word length to include (default: 3)

    Returns:
        pl.DataFrame with columns 'word' and 'count', sorted by count descending
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
    text_messages = df.filter(pl.col("message_type") == "text")["message"].to_list()

    for msg in text_messages:
        if msg is None:
            continue
        # Tokenize and filter
        tokens = token_re.findall(str(msg).lower())
        filtered = [t for t in tokens if len(t) >= min_word_length and t not in stopwords]
        all_words.extend(filtered)

    # Create frequency DataFrame using polars
    if not all_words:
        # Return empty DataFrame with correct schema
        return pl.DataFrame({"word": [], "count": []}, schema={"word": pl.Utf8, "count": pl.UInt32})

    # Create series and get value counts - returns a DataFrame with "word" and "count" columns
    word_series = pl.Series("word", all_words)
    word_freq_df = word_series.value_counts(sort=True)
    return word_freq_df


def get_word_count(text: str) -> int:
    """Count words in a message, excluding media placeholders."""
    if text is None:
        return 0
    # Remove URLs
    text = re.sub(r"https?://\S+", "", str(text))
    # Remove media omitted placeholders
    text = re.sub(r"\w+ omitted", "", text)
    words = text.split()
    return len(words)


def calculate_user_stats(
    df: pl.DataFrame, user_name: str, date_range: list[date] | None = None
) -> UserStats:
    """Calculate comprehensive statistics for a single user."""
    user_df = df.filter(pl.col("name") == user_name)

    # Basic counts
    total_messages = len(user_df)

    # Word count (reuse pre-calculated if available)
    if "word_count" not in user_df.columns:
        user_df = user_df.with_columns(
            pl.col("message")
            .str.replace_all(r"https?://\S+", "")  # Remove URLs
            .str.replace_all(r"\w+ omitted", "")   # Remove media placeholders
            .str.split(" ")
            .list.len()
            .fill_null(0)
            .alias("word_count")
        )
    total_words = user_df["word_count"].fill_null(0).sum()

    # Average message length (characters)
    text_messages = user_df.filter(pl.col("message_type") == "text")
    avg_message_length = text_messages["message"].str.len_chars().mean() if len(text_messages) > 0 else 0

    # Emoji analysis (reuse pre-extracted emojis if available)
    if "emojis" in user_df.columns:
        all_emojis = [emoji for emoji_list in user_df["emojis"].to_list() for emoji in emoji_list]
    else:
        all_emojis = []
        for msg in user_df["message"].to_list():
            all_emojis.extend(extract_emojis(str(msg) if msg is not None else ""))

    emoji_count = len(all_emojis)
    if all_emojis:
        emoji_series = pl.Series("emoji", all_emojis)
        emoji_freq = emoji_series.value_counts(sort=True)
        top_emojis = list(zip(emoji_freq["emoji"].head(7).to_list(), emoji_freq["count"].head(7).to_list(), strict=True))
    else:
        top_emojis = []

    # Daily activity for sparkline - normalized to full date range
    daily_counts = user_df.group_by(pl.col("timestamp").dt.date()).len().sort("timestamp")

    # If date_range is provided, create full date range and join
    if date_range is not None:
        # Create scaffold of all dates
        date_scaffold = pl.DataFrame({"date": date_range})
        # Join with actual counts
        daily_activity_df = date_scaffold.join(
            daily_counts.rename({"timestamp": "date"}),
            on="date",
            how="left"
        ).with_columns(
            pl.col("len").fill_null(0)
        )
        daily_activity = daily_activity_df["len"]
    else:
        daily_activity = daily_counts["len"]

    # Calculate longest silence (days between messages) using native Polars
    unique_dates_df = user_df.select(pl.col("timestamp").dt.date().unique().alias("date")).sort("date")
    if len(unique_dates_df) > 1:
        date_diffs_df = unique_dates_df.with_columns(
            (pl.col("date") - pl.col("date").shift(1)).alias("diff_days")
        )
        max_diff = date_diffs_df["diff_days"].drop_nulls().max()
        longest_silence = max_diff.days if max_diff is not None else 0
    else:
        longest_silence = 0

    # Calculate longest streak (consecutive days with messages) using native Polars
    if len(unique_dates_df) > 1:
        # Calculate day differences and mark streak breaks
        streak_df = unique_dates_df.with_columns(
            (pl.col("date") - pl.col("date").shift(1)).alias("diff")
        ).with_columns(
            # A new streak starts when diff is null (first row) or diff != 1 day
            pl.when(pl.col("diff").is_null())
            .then(pl.lit(1))
            .when(pl.col("diff").dt.total_days() != 1)
            .then(pl.lit(1))
            .otherwise(pl.lit(0))
            .alias("is_new_streak")
        ).with_columns(
            # Create streak groups using cumulative sum of streak breaks
            pl.col("is_new_streak").cum_sum().alias("streak_group")
        )
        # Count dates in each streak group
        streak_lengths = streak_df.group_by("streak_group").len()
        longest_streak = int(streak_lengths["len"].max() or 1)
    else:
        longest_streak = 1 if len(unique_dates_df) == 1 else 0

    # Most active hour
    hour_counts = user_df.group_by(pl.col("timestamp").dt.hour()).len().sort("len", descending=True)
    most_active_hour = hour_counts["timestamp"].head(1)[0] if len(hour_counts) > 0 else 12

    # Hourly activity distribution (0-23)
    hourly_counts = user_df.group_by(pl.col("timestamp").dt.hour()).len().sort("timestamp")
    # Create full 0-23 range
    hour_scaffold = pl.DataFrame({"hour": list(range(24))})
    hourly_activity_df = hour_scaffold.join(
        hourly_counts.rename({"timestamp": "hour"}),
        on="hour",
        how="left"
    ).with_columns(
        pl.col("len").fill_null(0)
    )
    hourly_activity = hourly_activity_df["len"]

    # Message type breakdown
    message_type_counts = user_df.group_by("message_type").len()
    message_types = dict(zip(message_type_counts["message_type"].to_list(),
                             message_type_counts["len"].to_list(), strict=True))

    # Activity category based on hour distribution (using native Polars for performance)
    hour_col = pl.col("timestamp").dt.hour()
    night_hours = user_df.filter(hour_col.is_between(0, 5, closed="both")).height
    morning_hours = user_df.filter(hour_col.is_between(6, 11, closed="both")).height
    afternoon_hours = user_df.filter(hour_col.is_between(12, 17, closed="both")).height
    evening_hours = user_df.filter(hour_col.is_between(18, 23, closed="both")).height

    if night_hours + evening_hours > morning_hours + afternoon_hours:
        activity_category = "night_owl"
    elif morning_hours > evening_hours:
        activity_category = "early_bird"
    else:
        activity_category = "balanced"

    return UserStats(
        name=user_name,
        total_messages=total_messages,
        total_words=int(total_words or 0),
        avg_message_length=round(avg_message_length, 1) if avg_message_length is not None else 0.0,
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


def analyze_chat(df: pl.DataFrame) -> ChatAnalytics:
    """
    Perform comprehensive analysis on a WhatsApp chat DataFrame.

    Args:
        df: Parsed chat DataFrame with columns: timestamp, name, message, message_type

    Returns:
        ChatAnalytics object with all computed statistics
    """
    # Overview stats
    total_messages = len(df)
    total_members = df["name"].n_unique()

    date_range = df["timestamp"].max() - df["timestamp"].min()
    num_days = max(date_range.days, 1)
    messages_per_day = round(total_messages / num_days, 1)

    # Calculate total words using native Polars expressions (faster than map_elements)
    df = df.with_columns(
        pl.col("message")
        .str.replace_all(r"https?://\S+", "")  # Remove URLs
        .str.replace_all(r"\w+ omitted", "")   # Remove media placeholders
        .str.split(" ")
        .list.len()
        .fill_null(0)
        .alias("word_count")
    )
    total_words = int(df["word_count"].sum() or 0)

    # Extract emojis once for reuse in user stats and overall stats
    # Note: Using map_elements here due to complex emoji handling (ZWJ sequences, skin tones, etc.)
    # A simpler str.extract_all approach could be used if emoji complexity is not needed
    df = df.with_columns(
        pl.col("message").map_elements(lambda msg: extract_emojis(str(msg) if msg is not None else ""),
                                       return_dtype=pl.List(pl.Utf8)).alias("emojis")
    )

    # Time-based aggregations - return as DataFrames with proper column names
    hourly_counts = df.group_by(pl.col("timestamp").dt.hour()).len().sort("timestamp")
    # Create full 0-23 range
    hour_scaffold = pl.DataFrame({"hour": list(range(24))})
    messages_by_hour = hour_scaffold.join(
        hourly_counts.rename({"timestamp": "hour", "len": "count"}),
        on="hour",
        how="left"
    ).with_columns(pl.col("count").fill_null(0))

    # polars weekday() returns 1-7 where 1=Monday, 7=Sunday
    weekday_counts = df.group_by(pl.col("timestamp").dt.weekday()).len().sort("timestamp")
    # Create DataFrame with weekday numbers 1-7 and names
    weekday_scaffold = pl.DataFrame({
        "weekday_num": list(range(1, 8)),
        "weekday": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    })
    messages_by_weekday = weekday_scaffold.join(
        weekday_counts.rename({"timestamp": "weekday_num", "len": "count"}),
        on="weekday_num",
        how="left"
    ).with_columns(pl.col("count").fill_null(0)).select(["weekday", "count"])

    messages_by_date = df.group_by(pl.col("timestamp").dt.date()).len().sort("timestamp").rename({"timestamp": "date", "len": "count"})

    # Extract year-month as string for grouping
    df_with_month = df.with_columns(
        pl.col("timestamp").dt.strftime("%Y-%m").alias("month")
    )
    messages_by_month = df_with_month.group_by("month").len().sort("month").rename({"len": "count"})

    # Most active day/hour
    max_weekday_row = messages_by_weekday.sort("count", descending=True).head(1)
    most_active_day = max_weekday_row["weekday"][0]
    max_hour_row = messages_by_hour.sort("count", descending=True).head(1)
    most_active_hour = max_hour_row["hour"][0]

    # Create full date range for normalized sparklines
    min_date = df["timestamp"].min().date()
    max_date = df["timestamp"].max().date()
    # Create list of dates from min to max
    full_date_range = pl.date_range(min_date, max_date, interval="1d", eager=True).cast(pl.Date).to_list()

    # User statistics with normalized date range
    user_names = df["name"].unique().to_list()
    user_stats = [calculate_user_stats(df, name, full_date_range) for name in user_names]
    user_stats.sort(key=lambda x: x.total_messages, reverse=True)

    top_messagers = [(u.name, u.total_messages) for u in user_stats]

    # Hourly activity by user (for heatmap)
    hourly_by_user_raw = df.group_by(["name", pl.col("timestamp").dt.hour()]).len()
    # Pivot to get users as rows, hours as columns
    # Note: Polars pivot creates column names from the hour values (0-23) as strings
    hourly_by_user = hourly_by_user_raw.pivot(
        index="name",
        on="timestamp",
        values="len"
    ).fill_null(0)
    # Ensure all 24 hours are present as columns (pivot may skip hours with no messages)
    for hour in range(24):
        hour_str = str(hour)  # Pivot creates string column names "0", "1", ..., "23"
        if hour_str not in hourly_by_user.columns:
            hourly_by_user = hourly_by_user.with_columns(pl.lit(0).alias(hour_str))
    # Sort columns by hour
    hour_cols = [str(h) for h in range(24)]
    available_hour_cols = [c for c in hour_cols if c in hourly_by_user.columns]
    hourly_by_user = hourly_by_user.select(["name"] + available_hour_cols)

    # Message type stats
    message_type_counts = df.group_by("message_type").len().sort("len", descending=True).rename({"len": "count"})

    message_type_by_user_raw = df.group_by(["name", "message_type"]).len()
    message_type_by_user = message_type_by_user_raw.pivot(
        index="name",
        on="message_type",
        values="len"
    ).fill_null(0)

    # Emoji stats (reuse pre-extracted emojis)
    if "emojis" in df.columns:
        all_emojis = [emoji for emoji_list in df["emojis"].to_list() for emoji in emoji_list]
    else:
        all_emojis = []
        for msg in df["message"].to_list():
            all_emojis.extend(extract_emojis(str(msg) if msg is not None else ""))

    if all_emojis:
        emoji_series = pl.Series("emoji", all_emojis)
        emoji_freq = emoji_series.value_counts(sort=True)
        top_emojis_overall = list(zip(emoji_freq["emoji"].head(10).to_list(),
                                      emoji_freq["count"].head(10).to_list(), strict=True))
        emoji_diversity = len(emoji_freq)
    else:
        top_emojis_overall = []
        emoji_diversity = 0

    # Word frequencies for word cloud
    word_frequencies = extract_word_frequencies(df)

    # Special stats
    busiest_date_row = messages_by_date.sort("count", descending=True).head(1)
    busiest_date = busiest_date_row["date"][0]
    busiest_day = (str(busiest_date), int(busiest_date_row["count"][0]))

    # Filter out days with 0 messages for quietest day
    active_days_df = messages_by_date.filter(pl.col("count") > 0)
    if len(active_days_df) > 0:
        quietest_date_row = active_days_df.sort("count").head(1)
        quietest_date = quietest_date_row["date"][0]
        quietest_day = (str(quietest_date), int(quietest_date_row["count"][0]))
    else:
        quietest_day = ("N/A", 0)

    # Longest conversation: day with most unique participants and messages
    daily_stats = df.group_by(pl.col("timestamp").dt.date()).agg([
        pl.count("message").alias("messages"),
        pl.col("name").n_unique().alias("participants")
    ]).rename({"timestamp": "date"})
    daily_stats = daily_stats.with_columns(
        (pl.col("messages") * pl.col("participants")).alias("score")
    )
    best_day_row = daily_stats.sort("score", descending=True).head(1)
    best_day_date = best_day_row["date"][0]

    # Format date as human-readable
    formatted_date = datetime.strptime(str(best_day_date), "%Y-%m-%d").strftime("%B %d, %Y")

    longest_conversation = {
        "date": formatted_date,
        "messages": int(best_day_row["messages"][0]),
        "participants": int(best_day_row["participants"][0]),
    }

    # Total stickers
    sticker_row = message_type_counts.filter(pl.col("message_type") == "sticker")
    total_stickers = int(sticker_row["count"][0]) if len(sticker_row) > 0 else 0

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
        # hourly_activity is a Series of length 24 (indices 0-23)
        night_indices = list(range(0, 6)) + list(range(18, 24))
        night_hours = user.hourly_activity.gather(night_indices).sum()
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
        # hourly_activity is a Series of length 24 (indices 0-23)
        morning_indices = list(range(6, 12))
        morning_hours = user.hourly_activity.gather(morning_indices).sum()
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
