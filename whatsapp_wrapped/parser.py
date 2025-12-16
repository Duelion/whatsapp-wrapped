"""
WhatsApp Chat Parser Module

Extracts and parses WhatsApp chat exports from .zip or .txt files.
Handles multiple date formats and classifies message types.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

import polars as pl


@dataclass
class ChatMetadata:
    """Metadata about the parsed chat."""

    filename: str
    total_messages: int
    total_members: int
    date_range_start: datetime
    date_range_end: datetime
    member_names: list[str]


# Common WhatsApp date formats across different locales
DATE_FORMATS = [
    "%d-%m-%y, %H:%M:%S",  # DD-MM-YY, HH:MM:SS (common in many regions)
    "%d/%m/%y, %H:%M:%S",  # DD/MM/YY, HH:MM:SS
    "%m/%d/%y, %H:%M:%S",  # MM/DD/YY, HH:MM:SS (US format)
    "%d-%m-%Y, %H:%M:%S",  # DD-MM-YYYY, HH:MM:SS
    "%d/%m/%Y, %H:%M:%S",  # DD/MM/YYYY, HH:MM:SS
    "%m/%d/%Y, %H:%M:%S",  # MM/DD/YYYY, HH:MM:SS
    "%d-%m-%y, %H:%M",  # Without seconds
    "%d/%m/%y, %H:%M",
    "%m/%d/%y, %H:%M",
    "%Y-%m-%d, %H:%M:%S",  # ISO-ish format
    "%d.%m.%y, %H:%M:%S",  # German format with dots
    "%d.%m.%Y, %H:%M:%S",
    # 12-hour AM/PM formats
    "%m/%d/%y, %I:%M:%S %p",  # US 12-hour with seconds: 12/25/23, 3:45:30 PM
    "%m/%d/%y, %I:%M %p",  # US 12-hour: 12/25/23, 3:45 PM
    "%d/%m/%y, %I:%M:%S %p",  # EU 12-hour with seconds
    "%d/%m/%y, %I:%M %p",  # EU 12-hour
    "%m/%d/%Y, %I:%M:%S %p",  # US 12-hour 4-digit year with seconds
    "%m/%d/%Y, %I:%M %p",  # US 12-hour 4-digit year
    "%d/%m/%Y, %I:%M:%S %p",  # EU 12-hour 4-digit year with seconds
    "%d/%m/%Y, %I:%M %p",  # EU 12-hour 4-digit year
    "%d-%m-%y, %I:%M:%S %p",  # DD-MM-YY 12-hour with seconds
    "%d-%m-%y, %I:%M %p",  # DD-MM-YY 12-hour
    "%d-%m-%Y, %I:%M:%S %p",  # DD-MM-YYYY 12-hour with seconds
    "%d-%m-%Y, %I:%M %p",  # DD-MM-YYYY 12-hour
    # Year-first formats (Asian locales: Japan, China, Korea, Hungary)
    "%Y/%m/%d, %H:%M:%S",  # YYYY/MM/DD 24-hour: 2024/01/28, 15:30:00
    "%Y/%m/%d, %H:%M",  # YYYY/MM/DD without seconds
    "%Y-%m-%d, %I:%M:%S %p",  # Year-first 12-hour: 2024-01-28, 3:30:00 PM
    "%Y-%m-%d, %I:%M %p",  # Year-first 12-hour without seconds
    "%Y/%m/%d, %I:%M:%S %p",  # Year-first slashes 12-hour
    "%Y/%m/%d, %I:%M %p",  # Year-first slashes 12-hour without seconds
    "%Y.%m.%d, %H:%M:%S",  # Year-first dots 24-hour
    "%Y.%m.%d, %H:%M",  # Year-first dots without seconds
    "%Y.%m.%d, %I:%M:%S %p",  # Year-first dots 12-hour
    "%Y.%m.%d, %I:%M %p",  # Year-first dots 12-hour without seconds
    # German dots with 12-hour AM/PM
    "%d.%m.%y, %I:%M:%S %p",  # DD.MM.YY 12-hour: 28.01.24, 3:30:00 PM
    "%d.%m.%y, %I:%M %p",  # DD.MM.YY 12-hour without seconds
    "%d.%m.%Y, %I:%M:%S %p",  # DD.MM.YYYY 12-hour with seconds
    "%d.%m.%Y, %I:%M %p",  # DD.MM.YYYY 12-hour without seconds
    # No-comma variants (space-only separator) - Brazilian, some Android versions
    "%d/%m/%y %H:%M:%S",  # DD/MM/YY space separator: 28/01/24 15:30:00
    "%d/%m/%y %H:%M",  # DD/MM/YY space separator without seconds
    "%m/%d/%y %H:%M:%S",  # MM/DD/YY space separator
    "%m/%d/%y %H:%M",  # MM/DD/YY space separator without seconds
    "%d-%m-%y %H:%M:%S",  # DD-MM-YY space separator
    "%d-%m-%y %H:%M",  # DD-MM-YY space separator without seconds
    "%d-%m-%Y %H:%M:%S",  # DD-MM-YYYY space separator (4-digit year)
    "%d-%m-%Y %H:%M",  # DD-MM-YYYY space separator without seconds
    "%d/%m/%Y %H:%M:%S",  # DD/MM/YYYY space separator
    "%d/%m/%Y %H:%M",  # DD/MM/YYYY space separator without seconds
    "%m/%d/%Y %H:%M:%S",  # MM/DD/YYYY space separator
    "%m/%d/%Y %H:%M",  # MM/DD/YYYY space separator without seconds
    "%d.%m.%y %H:%M:%S",  # German dots space separator
    "%d.%m.%y %H:%M",  # German dots space separator without seconds
    "%d.%m.%Y %H:%M:%S",  # German dots space separator 4-digit year
    "%d.%m.%Y %H:%M",  # German dots space separator 4-digit year without seconds
    # 12-hour with space separator
    "%d/%m/%y %I:%M:%S %p",  # DD/MM/YY space 12-hour
    "%d/%m/%y %I:%M %p",  # DD/MM/YY space 12-hour without seconds
    "%m/%d/%y %I:%M:%S %p",  # MM/DD/YY space 12-hour
    "%m/%d/%y %I:%M %p",  # MM/DD/YY space 12-hour without seconds
    "%d/%m/%Y %I:%M:%S %p",  # DD/MM/YYYY space 12-hour
    "%d/%m/%Y %I:%M %p",  # DD/MM/YYYY space 12-hour without seconds
    "%m/%d/%Y %I:%M:%S %p",  # MM/DD/YYYY space 12-hour
    "%m/%d/%Y %I:%M %p",  # MM/DD/YYYY space 12-hour without seconds
    # ISO 8601 with T separator (technical exports)
    "%Y-%m-%dT%H:%M:%S",  # ISO 8601: 2024-01-28T15:30:00
    "%Y-%m-%dT%H:%M",  # ISO 8601 without seconds
]

# Pattern to match WhatsApp message lines
# Handles formats like: [DD-MM-YY, HH:MM:SS] Name: Message
# Or: DD/MM/YY, HH:MM - Name: Message
# Or: YYYY-MM-DD, HH:MM - Name: Message (year-first Asian formats)
# Or: 2024-01-28T15:30:00 - Name: Message (ISO 8601)
# System messages don't have the "Name:" part
MESSAGE_PATTERNS = [
    r"\[(.+?)\] (.+?):\s*(.*)",  # [timestamp] name: message (iOS export)
    # Android export: unified pattern to handle ALL date/time variations (year-first, day-first, month-first)
    # Matches: YYYY-MM-DD, DD-MM-YY, MM/DD/YY, etc., with comma/space/T separator, time with :/., optional AM/PM with/without dots
    r"(\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}[,\sT]+\d{1,2}[:\.]?\d{2}(?:[:\.]?\d{2})?(?:\s*[APap]\.?[Mm]\.?)?)\s*-\s*(.+?):\s*(.*)",
]

# Patterns for system messages (no author/colon)
SYSTEM_MESSAGE_PATTERNS = [
    r"\[(.+?)\] (.+)$",  # [timestamp] system message (iOS export)
    # Android system messages: same unified pattern as user messages
    r"(\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}[,\sT]+\d{1,2}[:\.]?\d{2}(?:[:\.]?\d{2})?(?:\s*[APap]\.?[Mm]\.?)?)\s*-\s*(.+)$",
]


def load_chat_file(file_path: str | Path) -> str:
    """
    Load WhatsApp chat from a .zip or .txt file.

    Args:
        file_path: Path to the chat export file (.zip or .txt)

    Returns:
        Raw chat text content
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Chat file not found: {file_path}")

    if file_path.suffix.lower() == ".zip":
        return _load_from_zip(file_path)
    elif file_path.suffix.lower() == ".txt":
        return _load_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")


def _load_from_zip(zip_path: Path) -> str:
    """Extract and read chat text from a WhatsApp .zip export."""
    with ZipFile(zip_path) as zf:
        # Look for the chat file (usually _chat.txt or chat.txt)
        chat_files = [f for f in zf.namelist() if f.endswith(".txt") and "chat" in f.lower()]

        if not chat_files:
            # Fallback: look for any .txt file
            chat_files = [f for f in zf.namelist() if f.endswith(".txt")]

        if not chat_files:
            raise ValueError("No chat text file found in the zip archive")

        # Read the first matching file
        chat_binary = zf.read(chat_files[0])

        # Try different encodings
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                return chat_binary.decode(encoding)
            except UnicodeDecodeError:
                continue

        raise ValueError("Could not decode chat file with any supported encoding")


def _load_from_txt(txt_path: Path) -> str:
    """Read chat text from a .txt file."""
    for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
        try:
            return txt_path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue

    raise ValueError("Could not decode chat file with any supported encoding")


def _parse_timestamp(
    timestamp_str: str,
    date_formats: list[str] | None = None,
    cached_format: list[str | None] | None = None,
) -> datetime | None:
    """Try to parse a timestamp string using various formats.

    Args:
        timestamp_str: The timestamp string to parse
        date_formats: List of date format strings to try. If None, uses DATE_FORMATS.
        cached_format: Mutable list containing cached format from previous successful parse.
                      Pass as [None] initially, will be updated to [format_str] on success.

    Returns:
        Parsed datetime object or None if parsing fails
    """
    if date_formats is None:
        date_formats = DATE_FORMATS

    timestamp_str = timestamp_str.strip()

    # Normalize AM/PM variations (e.g., "am" -> "AM", "11PM" -> "11 PM", "3:30 A.M." -> "3:30 AM")
    # Handle A.M./P.M. with periods first
    timestamp_str = re.sub(r"([APap])\.([Mm])\.", r"\1\2", timestamp_str)  # A.M./P.M. -> AM/PM
    timestamp_str = re.sub(r"(\d)([APap][Mm])", r"\1 \2", timestamp_str)  # Add space before AM/PM
    timestamp_str = re.sub(
        r"\b([APap][Mm])\b", lambda m: m.group(1).upper(), timestamp_str
    )  # Uppercase AM/PM

    # Normalize dot time separators to colons (e.g., "15.30.00" -> "15:30:00", Finnish/Baltic format)
    # Look for time pattern after comma or space: HH.MM.SS or HH.MM
    # Only replace dots that come after the date part (after comma or space)
    if re.search(r"[,\s]\d{1,2}\.\d{2}", timestamp_str):
        # Has dot time separator - replace dots with colons only in time part
        parts = re.split(r"([,\s]+)", timestamp_str, maxsplit=1)
        if len(parts) >= 3:
            # parts[0] = date, parts[1] = separator, parts[2] = time
            time_part = parts[2]
            time_part = re.sub(r"\.", ":", time_part)  # Replace all dots in time with colons
            timestamp_str = parts[0] + parts[1] + time_part

    # Try cached format first if available
    if cached_format and cached_format[0]:
        try:
            return datetime.strptime(timestamp_str, cached_format[0])
        except ValueError:
            pass  # Cache miss, fall through to try all formats

    # Try all formats
    for fmt in date_formats:
        try:
            result = datetime.strptime(timestamp_str, fmt)
            # Cache the successful format for future calls
            if cached_format is not None:
                cached_format[0] = fmt
            return result
        except ValueError:
            continue

    return None


def _detect_date_order(raw_text: str) -> str:
    """
    Detect whether dates are in DD/MM or MM/DD format by analyzing the chat.

    Returns:
        "DD/MM" if day-first format detected
        "MM/DD" if month-first format detected
        "ambiguous" if cannot be determined
    """
    # Extract all date-like patterns
    date_pattern = r"(\d{1,2})[-/\.](\d{1,2})[-/\.](\d{2,4})"
    matches = re.findall(date_pattern, raw_text)

    has_first_over_12 = False
    has_second_over_12 = False

    for d1, d2, _year in matches:
        d1_int = int(d1)
        d2_int = int(d2)

        if d1_int > 12:
            has_first_over_12 = True
        if d2_int > 12:
            has_second_over_12 = True

    # If first component > 12, it must be DD/MM
    if has_first_over_12 and not has_second_over_12:
        return "DD/MM"

    # If second component > 12, it must be MM/DD
    if has_second_over_12 and not has_first_over_12:
        return "MM/DD"

    # If both have values > 12, something is wrong (shouldn't happen)
    # If neither has values > 12, we can't determine
    return "ambiguous"


# Media keywords mapped to their type - used for language-agnostic detection
# If a short message (2-3 words) starts with one of these, it's a media placeholder
MEDIA_KEYWORDS = {
    "video": "video",
    "vídeo": "video",
    "image": "image",
    "imagen": "image",
    "foto": "image",
    "photo": "image",
    "audio": "audio",
    "sticker": "sticker",
    "gif": "gif",
    "document": "document",
    "documento": "document",
    "contact": "contact",  # handles "contact card ..."
    "media": "image",  # generic <Media omitted>
    "location": "location",
    "ubicación": "location",
}


def _classify_message_type(message: str) -> str:
    """
    Classify the type of a WhatsApp message.

    Uses a language-agnostic approach: if a short message (2-3 words) starts with
    a media keyword, it's treated as that media type regardless of language.

    Returns one of: 'text', 'image', 'video', 'audio', 'sticker', 'gif', 'link', 'document', 'contact', 'location'
    """
    # Strip Unicode direction marks (LRM/RLM) that WhatsApp adds
    clean_msg = message.strip("\u200e\u200f").strip()

    # Handle angle bracket format: <Media omitted>
    if clean_msg.startswith("<") and clean_msg.endswith(">"):
        clean_msg = clean_msg[1:-1].strip()

    # Check for links first (they can be longer)
    if re.search(r"https?://", message):
        return "link"

    # Split into words and check if it's a short media placeholder
    words = clean_msg.lower().split()

    # Media placeholders are 1-3 words with a media keyword as first word
    if 1 <= len(words) <= 3:
        first_word = words[0]
        if first_word in MEDIA_KEYWORDS:
            return MEDIA_KEYWORDS[first_word]

    return "text"


def parse_chat(raw_text: str) -> pl.DataFrame:
    """
    Parse raw WhatsApp chat text into a structured DataFrame.

    Args:
        raw_text: Raw chat text content

    Returns:
        DataFrame with columns: timestamp, name, message, message_type
    """
    messages = []

    # Split by newlines that start a new message (with timestamp)
    # Handle both \r\n and \n line endings
    raw_text = raw_text.replace("\r\n", "\n")

    # Detect date order (DD/MM vs MM/DD) to prioritize correct formats
    date_order = _detect_date_order(raw_text)

    # Create a local reordered copy of DATE_FORMATS based on detected order
    date_formats_to_use = DATE_FORMATS.copy()

    if date_order == "DD/MM":
        # Prioritize DD/MM formats (those starting with %d), keep year-first and ISO formats
        dd_first = [f for f in DATE_FORMATS if f.startswith("%d")]
        mm_first = [f for f in DATE_FORMATS if f.startswith("%m")]
        year_first = [f for f in DATE_FORMATS if f.startswith("%Y")]
        date_formats_to_use = dd_first + year_first + mm_first
    elif date_order == "MM/DD":
        # Prioritize MM/DD formats (those starting with %m), keep year-first and ISO formats
        mm_first = [f for f in DATE_FORMATS if f.startswith("%m")]
        dd_first = [f for f in DATE_FORMATS if f.startswith("%d")]
        year_first = [f for f in DATE_FORMATS if f.startswith("%Y")]
        date_formats_to_use = mm_first + year_first + dd_first
    # If ambiguous, keep original order (DD/MM first by default)

    # Try different patterns to find the right one for this export
    for pattern_idx, pattern in enumerate(MESSAGE_PATTERNS):
        # Split text into potential message blocks
        # Messages can span multiple lines, so we need to handle continuations
        lines = raw_text.split("\n")

        current_message = None
        cached_format = [None]  # Mutable cache for date format

        for line in lines:
            # Strip Unicode direction marks (LRM/RLM) that can appear at line start
            line = line.lstrip("\u200e\u200f")

            match = re.match(pattern, line)

            # If user message pattern doesn't match, try system message pattern
            is_system = False
            if not match and pattern_idx < len(SYSTEM_MESSAGE_PATTERNS):
                system_pattern = SYSTEM_MESSAGE_PATTERNS[pattern_idx]
                match = re.match(system_pattern, line)
                is_system = True

            if match:
                # Save previous message if exists
                if current_message:
                    messages.append(current_message)

                if is_system:
                    # System message: timestamp, message_text
                    timestamp_str, message = match.groups()
                    name = "System"  # Mark as system message
                else:
                    # User message: timestamp, name, message
                    timestamp_str, name, message = match.groups()

                timestamp = _parse_timestamp(timestamp_str, date_formats_to_use, cached_format)

                if timestamp:
                    current_message = {
                        "timestamp": timestamp,
                        "name": name.strip(),
                        "message": message.strip(),
                    }
                else:
                    # If we can't parse the timestamp, treat as continuation
                    if current_message:
                        current_message["message"] += "\n" + line.strip()
            elif current_message:
                # Continuation of previous message
                current_message["message"] += "\n" + line.strip()

        # Don't forget the last message
        if current_message:
            messages.append(current_message)

        # If we found messages with this pattern, we're done
        if messages:
            break

    if not messages:
        raise ValueError(
            "Could not parse any messages from the chat. The format may not be supported."
        )

    # Create DataFrame
    df = pl.DataFrame(messages)

    # Store original names and use cleaned names for analytics
    # Note: Assumes 'name_original' doesn't exist in the parsed messages
    # (which is guaranteed by our message parsing logic)
    df = df.with_columns([
        pl.col("name").alias("name_original"),
        pl.col("name").str.replace_all(r"[^\w\s]", "").str.strip_chars().alias("name")
    ])

    # Classify message types using language-agnostic heuristic:
    # If a short message (2-3 words) starts with a media keyword, it's that media type.
    # This works across all WhatsApp localizations without needing translation lists.
    #
    # Pattern structure: ^[\u200e\u200f]*<?(keyword)(\s+\S+){1,2}>?$
    # - Optional unicode direction marks at start
    # - Optional < bracket
    # - Media keyword
    # - 1-2 more words (so total 2-3 words)
    # - Optional > bracket

    # Normalize: strip unicode marks, lowercase for matching
    msg_normalized = (
        pl.col("message")
        .str.strip_chars("\u200e\u200f")
        .str.strip_chars()
        .str.to_lowercase()
    )

    df = df.with_columns(
        # Image: image, imagen, foto, photo, media (generic)
        pl.when(msg_normalized.str.contains(r"^<?(image|imagen|foto|photo|media)(\s+\S+){1,2}>?$"))
        .then(pl.lit("image"))
        # Video: video, vídeo
        .when(msg_normalized.str.contains(r"^<?(video|vídeo)(\s+\S+){1,2}>?$"))
        .then(pl.lit("video"))
        # Audio: audio
        .when(msg_normalized.str.contains(r"^<?audio(\s+\S+){1,2}>?$"))
        .then(pl.lit("audio"))
        # Sticker
        .when(msg_normalized.str.contains(r"^<?sticker(\s+\S+){1,2}>?$"))
        .then(pl.lit("sticker"))
        # GIF
        .when(msg_normalized.str.contains(r"^<?gif(\s+\S+){1,2}>?$"))
        .then(pl.lit("gif"))
        # Document: document, documento
        .when(msg_normalized.str.contains(r"^<?(document|documento)(\s+\S+){1,2}>?$"))
        .then(pl.lit("document"))
        # Contact: contact (handles "contact card omitted" - 3 words)
        .when(msg_normalized.str.contains(r"^<?contact(\s+\S+){1,2}>?$"))
        .then(pl.lit("contact"))
        # Location: location, ubicación (these use colon format)
        .when(msg_normalized.str.contains(r"^<?(location|ubicación):"))
        .then(pl.lit("location"))
        # Links (check original message for URLs)
        .when(pl.col("message").str.contains(r"https?://"))
        .then(pl.lit("link"))
        .otherwise(pl.lit("text"))
        .alias("message_type")
    )

    # Sort by timestamp
    df = df.sort("timestamp")

    return df


def filter_system_messages(df: pl.DataFrame) -> pl.DataFrame:
    """
    Remove system messages (group changes, etc.) from the DataFrame.

    Args:
        df: Parsed chat DataFrame

    Returns:
        DataFrame with system messages removed
    """
    system_patterns = [
        r"añadió a",
        r"added",
        r"removed",
        r"eliminó a",
        r"left",
        r"salió",
        r"changed the subject",
        r"cambió el asunto",
        r"changed this group",
        r"cambió el ícono",
        r"created group",
        r"creó el grupo",
        r"Messages and calls are end-to-end encrypted",
        r"Los mensajes y las llamadas están cifrados",
    ]

    pattern = "|".join(system_patterns)
    # Filter out messages containing system patterns
    return df.filter(~pl.col("message").str.contains(pattern, literal=False))


def filter_bot_users(df: pl.DataFrame) -> pl.DataFrame:
    """
    Remove bot and automated users (like Meta AI) from the DataFrame.

    Args:
        df: Parsed chat DataFrame

    Returns:
        DataFrame with bot users removed
    """
    bot_names = ["Meta AI", "meta ai"]

    # Filter out exact matches and case-insensitive matches
    bot_names_lower = [name.lower() for name in bot_names]
    return df.filter(~pl.col("name").str.to_lowercase().is_in(bot_names_lower))


def get_chat_metadata(df: pl.DataFrame, filename: str = "chat") -> ChatMetadata:
    """
    Extract metadata from a parsed chat DataFrame.

    Args:
        df: Parsed chat DataFrame
        filename: Original filename for reference

    Returns:
        ChatMetadata object with summary information
    """
    # Clean filename - remove .zip extension and clean up common patterns
    clean_filename = filename
    if clean_filename.endswith(".zip"):
        clean_filename = clean_filename[:-4]

    return ChatMetadata(
        filename=clean_filename,
        total_messages=len(df),
        total_members=df["name"].n_unique(),
        date_range_start=df["timestamp"].min(),
        date_range_end=df["timestamp"].max(),
        member_names=sorted(df["name"].unique().to_list()),
    )


def parse_whatsapp_export(
    file_path: str | Path,
    filter_system: bool = True,
    min_messages: int = 1,
    year_filter: int | None = None,
) -> tuple[pl.DataFrame, ChatMetadata]:
    """
    Main entry point: Parse a WhatsApp export file.

    Args:
        file_path: Path to .zip or .txt file
        filter_system: Whether to remove system messages
        min_messages: Minimum messages per user to include
        year_filter: Optional year to filter messages by

    Returns:
        Tuple of (DataFrame, ChatMetadata)
    """
    file_path = Path(file_path)

    # Load raw text
    raw_text = load_chat_file(file_path)

    # Parse into DataFrame
    df = parse_chat(raw_text)

    # Filter system messages
    if filter_system:
        df = filter_system_messages(df)

    # Filter bot users (Meta AI, etc.)
    df = filter_bot_users(df)

    # Filter by year if specified
    if year_filter:
        df = df.filter(pl.col("timestamp").dt.year() == year_filter)

    # Filter users with minimum messages
    if min_messages > 1:
        # Get user counts as a DataFrame
        user_counts = df.group_by("name").len().sort("len", descending=True)
        # Get users with at least min_messages
        valid_users = user_counts.filter(pl.col("len") >= min_messages)["name"].to_list()
        df = df.filter(pl.col("name").is_in(valid_users))

    # Get metadata
    metadata = get_chat_metadata(df, file_path.name)

    return df, metadata
