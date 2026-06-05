"""Tests for prompt templates."""

from __future__ import annotations

from terminal_triage.prompts import (
    MAX_OUTPUT_CHARS,
    build_analysis_prompt,
    build_question_prompt,
)


def test_analysis_prompt_includes_parts():
    prompt = build_analysis_prompt("kubectl get pods", "pod-1 Running", "an error")
    assert "kubectl get pods" in prompt
    assert "pod-1 Running" in prompt
    assert "an error" in prompt


def test_analysis_prompt_truncates_long_output():
    long_output = "x" * (MAX_OUTPUT_CHARS + 500)
    prompt = build_analysis_prompt("cmd", long_output, "")
    assert "truncated" in prompt
    assert long_output not in prompt


def test_analysis_prompt_includes_exit_code():
    prompt = build_analysis_prompt("kubectl get pods", "", "boom", returncode=1)
    assert "EXIT CODE: 1" in prompt


def test_analysis_prompt_exit_code_unknown_when_none():
    prompt = build_analysis_prompt("cmd", "out", "")
    assert "EXIT CODE: unknown" in prompt


def test_stderr_is_tail_truncated():
    # The real error is at the very end; head-truncation would drop it.
    stderr = ("noise\n" * MAX_OUTPUT_CHARS) + "FATAL: real error here"
    prompt = build_analysis_prompt("cmd", "", stderr, returncode=1)
    assert "FATAL: real error here" in prompt


def test_question_prompt_includes_question():
    prompt = build_question_prompt("how do I list pods?")
    assert "how do I list pods?" in prompt


def test_question_prompt_without_context_omits_recent_command():
    prompt = build_question_prompt("how do I list pods?")
    assert "most recent command" not in prompt


def test_question_prompt_includes_recent_command_context():
    prompt = build_question_prompt(
        "why did that fail?",
        command="kubectl get pods",
        stdout="",
        stderr="connection refused",
        returncode=1,
    )
    assert "why did that fail?" in prompt
    assert "kubectl get pods" in prompt
    assert "connection refused" in prompt
    assert "EXIT CODE: 1" in prompt
