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

import pandas as pd


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
]

# Pattern to match WhatsApp message lines
# Handles formats like: [DD-MM-YY, HH:MM:SS] Name: Message
# Or: DD/MM/YY, HH:MM - Name: Message
MESSAGE_PATTERNS = [
    r"\[(.+?)\] (.+?):\s*(.*)",  # [timestamp] name: message (iOS export)
    r"(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4},?\s*\d{1,2}:\d{2}(?::\d{2})?(?:\s*[APap][Mm])?)\s*-\s*(.+?):\s*(.*)",  # Android export
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


def _parse_timestamp(timestamp_str: str) -> datetime | None:
    """Try to parse a timestamp string using various formats."""
    timestamp_str = timestamp_str.strip()

    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue

    return None


def _classify_message_type(message: str) -> str:
    """
    Classify the type of a WhatsApp message.

    Returns one of: 'text', 'image', 'video', 'audio', 'sticker', 'gif', 'link', 'document', 'contact', 'location'
    """
    message_lower = message.lower()

    # Check for omitted media patterns
    omitted_patterns = {
        "image": ["image omitted", "imagen omitida", "<media omitted>"],
        "video": ["video omitted", "vídeo omitido"],
        "audio": ["audio omitted", "audio omitido"],
        "sticker": ["sticker omitted", "sticker omitido"],
        "gif": ["gif omitted", "gif omitido"],
        "document": ["document omitted", "documento omitido"],
        "contact": ["contact card omitted", "tarjeta de contacto omitida"],
        "location": ["location:", "ubicación:"],
    }

    for msg_type, patterns in omitted_patterns.items():
        for pattern in patterns:
            if pattern in message_lower:
                return msg_type

    # Check for links
    if re.search(r"https?://", message):
        return "link"

    return "text"


def parse_chat(raw_text: str) -> pd.DataFrame:
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

    # Try different patterns to find the right one for this export
    for pattern in MESSAGE_PATTERNS:
        # Split text into potential message blocks
        # Messages can span multiple lines, so we need to handle continuations
        lines = raw_text.split("\n")

        current_message = None

        for line in lines:
            match = re.match(pattern, line)

            if match:
                # Save previous message if exists
                if current_message:
                    messages.append(current_message)

                timestamp_str, name, message = match.groups()
                timestamp = _parse_timestamp(timestamp_str)

                if timestamp:
                    current_message = {
                        "timestamp": timestamp,
                        "name": name.strip(),
                        "message": message.strip(),
                    }
                else:
                    # If we can't parse the timestamp, treat as continuation
                    if current_message:
                        current_message["message"] += "\n" + line
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
    df = pd.DataFrame(messages)

    # Store original names and use cleaned names for analytics
    df["name_original"] = df["name"]
    df["name"] = df["name"].str.replace(r"[^\w\s]", "", regex=True).str.strip()

    # Classify message types
    df["message_type"] = df["message"].apply(_classify_message_type)

    # Sort by timestamp
    df = df.sort_values("timestamp").reset_index(drop=True)

    return df


def filter_system_messages(df: pd.DataFrame) -> pd.DataFrame:
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
    mask = df["message"].str.contains(pattern, case=False, regex=True, na=False)

    return df[~mask].copy()


def filter_bot_users(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove bot and automated users (like Meta AI) from the DataFrame.

    Args:
        df: Parsed chat DataFrame

    Returns:
        DataFrame with bot users removed
    """
    bot_names = ["Meta AI", "meta ai"]
    
    # Filter out exact matches and case-insensitive matches
    mask = df["name"].str.lower().isin([name.lower() for name in bot_names])
    
    return df[~mask].copy()


def get_chat_metadata(df: pd.DataFrame, filename: str = "chat") -> ChatMetadata:
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
    if clean_filename.endswith('.zip'):
        clean_filename = clean_filename[:-4]
    
    return ChatMetadata(
        filename=clean_filename,
        total_messages=len(df),
        total_members=df["name"].nunique(),
        date_range_start=df["timestamp"].min(),
        date_range_end=df["timestamp"].max(),
        member_names=sorted(df["name"].unique().tolist()),
    )


def parse_whatsapp_export(
    file_path: str | Path,
    filter_system: bool = True,
    min_messages: int = 1,
    year_filter: int | None = None,
) -> tuple[pd.DataFrame, ChatMetadata]:
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
        df = df[df["timestamp"].dt.year == year_filter].copy()

    # Filter users with minimum messages
    if min_messages > 1:
        user_counts = df["name"].value_counts()
        valid_users = user_counts[user_counts >= min_messages].index
        df = df[df["name"].isin(valid_users)].copy()

    # Reset index after filtering
    df = df.reset_index(drop=True)

    # Get metadata
    metadata = get_chat_metadata(df, file_path.name)

    return df, metadata
