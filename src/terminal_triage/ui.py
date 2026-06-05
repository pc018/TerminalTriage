"""ANSI color helpers for terminal output."""

from __future__ import annotations

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"


def color(text: str, code: str) -> str:
    """Wrap ``text`` in an ANSI color ``code`` and reset afterwards."""
    return f"{code}{text}{RESET}"
