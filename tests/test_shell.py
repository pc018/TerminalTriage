"""Tests for shell command execution."""

from __future__ import annotations

import sys

from terminal_triage.shell import run_command


def test_successful_command():
    result = run_command("echo hello")
    assert result.returncode == 0
    assert "hello" in result.stdout
    assert not result.failed


def test_empty_line():
    result = run_command("   ")
    assert result.returncode == 0
    assert not result.failed


def test_command_not_found():
    result = run_command("definitely-not-a-real-binary-xyz")
    assert result.error is not None
    assert "Command not found" in result.error
    assert result.failed


def test_nonzero_exit_is_failure():
    # `python -c 'sys.exit(3)'` is portable across platforms.
    result = run_command(f"{sys.executable} -c \"import sys; sys.exit(3)\"")
    assert result.returncode == 3
    assert result.failed


def test_stderr_captured():
    result = run_command(f"{sys.executable} -c \"import sys; sys.stderr.write('boom')\"")
    assert "boom" in result.stderr


def test_bad_quoting_reports_error():
    result = run_command('echo "unterminated')
    assert result.error is not None
    assert "Parse error" in result.error
