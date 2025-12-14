"""
WhatsApp Wrapped - A visualization project for WhatsApp group chats

Generate beautiful terminal-aesthetic reports from WhatsApp chat exports.
"""

__version__ = "1.0.0"

from .analytics import ChatAnalytics, UserStats, analyze_chat
from .charts import ChartCollection
from .generator import generate_full_report, generate_html_report, generate_pdf_report
from .parser import ChatMetadata, parse_whatsapp_export

__all__ = [
    "parse_whatsapp_export",
    "ChatMetadata",
    "analyze_chat",
    "ChatAnalytics",
    "UserStats",
    "ChartCollection",
    "generate_html_report",
    "generate_pdf_report",
    "generate_full_report",
]
