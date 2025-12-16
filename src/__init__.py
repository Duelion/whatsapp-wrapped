"""
WhatsApp Wrapped - A visualization project for WhatsApp group chats

Generate beautiful terminal-aesthetic reports from WhatsApp chat exports.

This module re-exports from the whatsapp_wrapped package for backward compatibility.
"""

__version__ = "1.0.0"

from whatsapp_wrapped.analytics import ChatAnalytics, UserStats, analyze_chat
from whatsapp_wrapped.charts import ChartCollection
from whatsapp_wrapped.generator import generate_full_report, generate_html_report
from whatsapp_wrapped.parser import ChatMetadata, parse_whatsapp_export

__all__ = [
    "parse_whatsapp_export",
    "ChatMetadata",
    "analyze_chat",
    "ChatAnalytics",
    "UserStats",
    "ChartCollection",
    "generate_html_report",
    "generate_full_report",
]
