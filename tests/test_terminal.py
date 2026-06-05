"""Tests for the REPL dispatch logic (no network, no prompt_toolkit loop)."""

from __future__ import annotations

import pytest

from terminal_triage.terminal import TriageTerminal


@pytest.fixture
def term(settings, fake_provider, recorder):
    return TriageTerminal(settings, provider=fake_provider, output=recorder)


def test_exit_and_quit(term):
    assert term.handle_line("exit") is True
    assert term.handle_line("quit") is True


def test_blank_line_is_noop(term):
    assert term.handle_line("   ") is False


def test_help(term, recorder):
    term.handle_line("help")
    assert "TerminalTriage commands" in recorder.text


def test_shell_passthrough(term, recorder):
    term.handle_line("echo hi")
    assert "hi" in recorder.text


def test_shell_without_analysis_does_not_call_provider(term, fake_provider):
    term.handle_line("echo hi")
    assert fake_provider.prompts == []


def test_claude_on_enables_analysis(term, recorder):
    term.handle_line("claude on")
    assert term.analysis_mode is True
    assert "ENABLED" in recorder.text


def test_claude_off_disables_analysis(term):
    term.handle_line("claude on")
    term.handle_line("claude off")
    assert term.analysis_mode is False


def test_analysis_streams_provider(term, fake_provider, recorder):
    term.handle_line("claude on")
    term.handle_line("echo hi")
    # Provider was asked to analyze the command output.
    assert len(fake_provider.prompts) == 1
    assert "echo hi" in fake_provider.prompts[0]
    assert "Looks" in recorder.text


def test_ai_question(term, fake_provider):
    term.handle_line("/ai how do I list pods?")
    assert len(fake_provider.prompts) == 1
    assert "how do I list pods?" in fake_provider.prompts[0]


def test_ai_without_question_shows_usage(term, recorder, fake_provider):
    term.handle_line("/ai")
    assert "Usage: /ai" in recorder.text
    assert fake_provider.prompts == []


def test_claude_unknown_arg_shows_usage(term, recorder):
    term.handle_line("claude maybe")
    assert "Usage: claude" in recorder.text


def test_provider_error_is_handled(settings, recorder):
    """If no provider can be built, AI commands fail gracefully."""
    # No provider injected and a provider that can't be constructed (fake
    # provider name has no factory entry) -> friendly error, no crash.
    settings.provider = "anthropic"
    settings.api_key = None  # missing key -> ProviderError in factory
    term = TriageTerminal(settings, provider=None, output=recorder)
    term.handle_line("/ai hello")
    assert "No API key" in recorder.text
