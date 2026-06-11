"""Tests for configuration loading."""

from __future__ import annotations

import pytest

from terminal_triage.config import DEFAULT_MODELS, load_settings


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for var in (
        "AI_PROVIDER",
        "AI_MODEL",
        "AI_MAX_TOKENS",
        "AI_HISTORY_FILE",
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "GEMINI_API_KEY",
        "CLAUDE_CODE_OAUTH_TOKEN",
    ):
        monkeypatch.delenv(var, raising=False)


def test_defaults():
    settings = load_settings(load_env=False)
    assert settings.provider == "anthropic"
    assert settings.model == DEFAULT_MODELS["anthropic"]
    assert settings.api_key is None
    assert settings.max_tokens == 4096


def test_provider_selects_key_and_model(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    settings = load_settings(load_env=False)
    assert settings.provider == "openai"
    assert settings.api_key == "sk-test"
    assert settings.model == DEFAULT_MODELS["openai"]


def test_explicit_model_overrides_default(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("AI_MODEL", "gemini-custom")
    settings = load_settings(load_env=False)
    assert settings.model == "gemini-custom"


def test_provider_is_case_insensitive(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "OpenAI")
    settings = load_settings(load_env=False)
    assert settings.provider == "openai"


def test_invalid_max_tokens_falls_back(monkeypatch):
    monkeypatch.setenv("AI_MAX_TOKENS", "not-a-number")
    settings = load_settings(load_env=False)
    assert settings.max_tokens == 4096


def test_anthropic_oauth_token_fallback(monkeypatch):
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "oat-token-123")
    settings = load_settings(load_env=False)
    assert settings.provider == "anthropic"
    assert settings.api_key is None
    assert settings.auth_token == "oat-token-123"


def test_anthropic_api_key_takes_precedence_over_oauth(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-real-key")
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "oat-token-123")
    settings = load_settings(load_env=False)
    assert settings.api_key == "sk-real-key"
    assert settings.auth_token is None
