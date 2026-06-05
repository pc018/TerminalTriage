"""Local shell command execution."""

from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass

DEFAULT_TIMEOUT = 30


@dataclass
class CommandResult:
    """Outcome of running a shell command."""

    command: str
    stdout: str = ""
    stderr: str = ""
    returncode: int | None = None
    error: str | None = None

    @property
    def failed(self) -> bool:
        """True if the command did not exit successfully."""
        return self.error is not None or (self.returncode not in (0, None))


def run_command(line: str, timeout: int = DEFAULT_TIMEOUT) -> CommandResult:
    """Run ``line`` as a shell command and capture its output.

    Never raises for normal command failures; problems (command not found,
    timeout, bad quoting) are reported via :attr:`CommandResult.error` so the
    caller can decide how to surface them.
    """
    line = line.strip()
    if not line:
        return CommandResult(command=line, returncode=0)

    try:
        args = shlex.split(line)
    except ValueError as exc:
        return CommandResult(command=line, error=f"Parse error: {exc}")

    if not args:
        return CommandResult(command=line, returncode=0)

    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return CommandResult(
            command=line,
            stdout=proc.stdout,
            stderr=proc.stderr,
            returncode=proc.returncode,
        )
    except FileNotFoundError:
        return CommandResult(command=line, error=f"Command not found: {args[0]}")
    except subprocess.TimeoutExpired:
        return CommandResult(command=line, error=f"Command timed out after {timeout}s")
    except Exception as exc:  # pragma: no cover - defensive catch-all
        return CommandResult(command=line, error=f"Execution error: {exc}")
