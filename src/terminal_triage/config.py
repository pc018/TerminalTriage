"""Configuration loading for TerminalTriage."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Provider -> default model when AI_MODEL is not set.
DEFAULT_MODELS: dict[str, str] = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.0-flash",
}

# Provider -> environment variable holding its API key.
API_KEY_ENV: dict[str, str] = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
}

DEFAULT_PROVIDER = "anthropic"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_HISTORY_FILE = "~/.terminal_triage_history"


@dataclass
class Settings:
    """Resolved runtime configuration."""

    provider: str
    api_key: str | None
    model: str
    max_tokens: int = DEFAULT_MAX_TOKENS
    history_file: Path = Path(DEFAULT_HISTORY_FILE).expanduser()
    auto_analyze: bool = False
    # When True, kubectl tab-completion delegates to ``kubectl __complete``, which
    # talks to the cluster. Off by default so completion stays fully offline.
    kubectl_live_completion: bool = False


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def load_settings(load_env: bool = True) -> Settings:
    """Build :class:`Settings` from environment variables and an optional ``.env``.

    Real environment variables take precedence over ``.env`` values.
    """
    if load_env:
        # override=False keeps real environment variables authoritative.
        load_dotenv(override=False)

    provider = (os.getenv("AI_PROVIDER") or DEFAULT_PROVIDER).strip().lower()

    key_env = API_KEY_ENV.get(provider)
    api_key = os.getenv(key_env) if key_env else None

    model = os.getenv("AI_MODEL") or DEFAULT_MODELS.get(provider, "")

    history_file = Path(
        os.getenv("AI_HISTORY_FILE") or DEFAULT_HISTORY_FILE
    ).expanduser()

    return Settings(
        provider=provider,
        api_key=api_key,
        model=model,
        max_tokens=_int_env("AI_MAX_TOKENS", DEFAULT_MAX_TOKENS),
        history_file=history_file,
        kubectl_live_completion=_bool_env("AI_KUBECTL_LIVE_COMPLETION", False),
    )
