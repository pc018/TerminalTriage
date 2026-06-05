"""Command-line entry point for TerminalTriage."""

from __future__ import annotations

import argparse
import os
import sys

from . import __version__
from .config import API_KEY_ENV, DEFAULT_MODELS, load_settings
from .terminal import TriageTerminal
from .ui import RED, RESET, YELLOW


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="triage",
        description="AI-powered interactive terminal for troubleshooting.",
    )
    parser.add_argument(
        "--provider",
        choices=sorted(DEFAULT_MODELS),
        help="AI provider to use (overrides AI_PROVIDER).",
    )
    parser.add_argument(
        "--model",
        help="Model to use (overrides AI_MODEL / the provider default).",
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Start with proactive AI analysis enabled.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    settings = load_settings()
    if args.provider:
        settings.provider = args.provider
        # Re-resolve the API key and default model for the chosen provider.
        key_env = API_KEY_ENV.get(args.provider)
        settings.api_key = os.getenv(key_env) if key_env else None
        settings.model = args.model or DEFAULT_MODELS.get(args.provider, settings.model)
    if args.model:
        settings.model = args.model
    if args.analyze:
        settings.auto_analyze = True

    if settings.api_key is None:
        print(
            f"{YELLOW}Warning: no API key found for provider "
            f"'{settings.provider}'. AI features will be unavailable until you "
            f"set one in your environment or .env file.{RESET}"
        )

    terminal = TriageTerminal(settings)
    try:
        terminal.run()
    except KeyboardInterrupt:
        print("\nExiting...")
        return 130
    except Exception as exc:  # pragma: no cover - top-level safety net
        print(f"{RED}Fatal error: {exc}{RESET}")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
