"""Re-export from whatsapp_wrapped.parser for backward compatibility."""

from whatsapp_wrapped.parser import *  # noqa: F401, F403
from whatsapp_wrapped.parser import ChatMetadata, parse_whatsapp_export

__all__ = ["parse_whatsapp_export", "ChatMetadata"]
