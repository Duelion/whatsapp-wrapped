"""Re-export from whatsapp_wrapped.generator for backward compatibility."""

from whatsapp_wrapped.generator import *  # noqa: F401, F403
from whatsapp_wrapped.generator import generate_full_report, generate_html_report

__all__ = ["generate_html_report", "generate_full_report"]
