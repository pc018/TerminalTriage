"""Prompt templates sent to the AI provider."""

from __future__ import annotations

# Cap how much command output we forward, to keep requests small and cheap.
MAX_OUTPUT_CHARS = 2000


def _truncate(text: str, limit: int = MAX_OUTPUT_CHARS, keep: str = "head") -> str:
    """Shorten ``text`` to ``limit`` chars.

    ``keep="head"`` retains the start (good for listings like ``kubectl get``);
    ``keep="tail"`` retains the end (good for stderr, where the actual error
    almost always sits at the bottom of the stream).
    """
    text = text or ""
    if len(text) <= limit:
        return text
    if keep == "tail":
        return "…(truncated)\n" + text[-limit:]
    return text[:limit] + "\n…(truncated)"


def _output_block(stdout: str, stderr: str, returncode: int | None) -> str:
    """Format a command's exit code and (truncated) output for a prompt."""
    status = "unknown" if returncode is None else str(returncode)
    return f"""EXIT CODE: {status}

STDOUT:
{_truncate(stdout)}

STDERR:
{_truncate(stderr, keep="tail")}"""


def build_analysis_prompt(
    command: str, stdout: str, stderr: str, returncode: int | None = None
) -> str:
    """Prompt asking the AI to analyze a command and its output."""
    return f"""You are assisting in a troubleshooting terminal used by developers and
system administrators (often working with Kubernetes, Docker, and Linux tools).

I just ran this command:
`{command}`

{_output_block(stdout, stderr, returncode)}

A non-zero exit code means the command failed. If there is an error, explain the
likely cause and how to fix it. If the output is successful, briefly summarize
what it shows. When useful, suggest a specific next command to run.
Keep the answer concise and actionable."""


def build_question_prompt(
    question: str,
    command: str | None = None,
    stdout: str = "",
    stderr: str = "",
    returncode: int | None = None,
) -> str:
    """Prompt for a free-form natural-language question (the ``/ai`` command).

    When ``command`` is given, the most recent command and its output are folded
    in as context so follow-up questions ("why did that fail?") work without the
    user re-pasting anything.
    """
    context = ""
    if command:
        context = f"""For context, the most recent command in this terminal was:
`{command}`

{_output_block(stdout, stderr, returncode)}

"""
    return f"""You are assisting in a troubleshooting terminal used by developers and
system administrators (Kubernetes, Docker, Linux). Answer the following question
concisely and practically, preferring concrete commands and steps.

{context}Question: {question}"""
