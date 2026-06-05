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


def test_question_prompt_includes_question():
    prompt = build_question_prompt("how do I list pods?")
    assert "how do I list pods?" in prompt
