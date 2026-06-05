"""Prompt templates sent to the AI provider."""

from __future__ import annotations

# Cap how much command output we forward, to keep requests small and cheap.
MAX_OUTPUT_CHARS = 2000


def _truncate(text: str, limit: int = MAX_OUTPUT_CHARS) -> str:
    text = text or ""
    if len(text) <= limit:
        return text
    return text[:limit] + "\n…(truncated)"


def build_analysis_prompt(command: str, stdout: str, stderr: str) -> str:
    """Prompt asking the AI to analyze a command and its output."""
    return f"""You are assisting in a troubleshooting terminal used by developers and
system administrators (often working with Kubernetes, Docker, and Linux tools).

I just ran this command:
`{command}`

STDOUT:
{_truncate(stdout)}

STDERR:
{_truncate(stderr)}

If there is an error, explain the likely cause and how to fix it.
If the output is successful, briefly summarize what it shows.
When useful, suggest a specific next command to run.
Keep the answer concise and actionable."""


def build_question_prompt(question: str) -> str:
    """Prompt for a free-form natural-language question (the ``/ai`` command)."""
    return f"""You are assisting in a troubleshooting terminal used by developers and
system administrators (Kubernetes, Docker, Linux). Answer the following question
concisely and practically, preferring concrete commands and steps.

Question: {question}"""
