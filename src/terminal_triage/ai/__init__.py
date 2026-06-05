"""AI provider abstraction for TerminalTriage."""

from __future__ import annotations

from .base import AIProvider
from .factory import get_provider

__all__ = ["AIProvider", "get_provider"]
