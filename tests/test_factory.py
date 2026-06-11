"""Tests for provider selection."""

from __future__ import annotations

import builtins

import pytest

from terminal_triage.ai.base import ProviderError
from terminal_triage.ai.factory import available_providers, get_provider
from terminal_triage.config import Settings


def _settings(**kw) -> Settings:
    base = dict(provider="anthropic", api_key="key", model="m")
    base.update(kw)
    return Settings(**base)


def test_available_providers():
    assert set(available_providers()) == {"anthropic", "openai", "gemini"}


def test_unknown_provider():
    with pytest.raises(ProviderError, match="Unknown AI provider"):
        get_provider(_settings(provider="nope"))


def test_missing_api_key():
    with pytest.raises(ProviderError, match="No API key"):
        get_provider(_settings(api_key=None))


def test_auth_token_bypasses_api_key_check(monkeypatch):
    """auth_token alone is sufficient — should reach SDK import, not auth check."""
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "anthropic" or name.startswith("anthropic."):
            raise ImportError("no anthropic")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    # Should raise SDK error, not "No API key" error.
    with pytest.raises(ProviderError, match="anthropic"):
        get_provider(_settings(api_key=None, auth_token="oat-token-123"))


def test_missing_sdk_message(monkeypatch):
    """If the vendor SDK isn't importable, a helpful ProviderError is raised."""
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "anthropic" or name.startswith("anthropic."):
            raise ImportError("no anthropic")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ProviderError, match="anthropic"):
        get_provider(_settings(provider="anthropic"))
