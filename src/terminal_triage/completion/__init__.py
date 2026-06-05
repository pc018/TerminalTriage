"""Auto-completion for the TerminalTriage REPL.

``build_completer`` merges several layers:

* built-in commands (``/ai``, ``ai on|off``, ``/claude``, ``help``, ``exit`` …),
* executables found on ``$PATH`` (first word only),
* filesystem paths (later words),
* the dedicated :class:`~terminal_triage.completion.kubectl.KubectlCompleter`.
"""

from __future__ import annotations

import os
from functools import lru_cache

from prompt_toolkit.completion import Completer, Completion, PathCompleter, merge_completers
from prompt_toolkit.document import Document

from .kubectl import KubectlCompleter

BUILTIN_COMMANDS: list[str] = [
    "/ai",
    "/claude",
    "/openai",
    "/gemini",
    "ai on",
    "ai off",
    "help",
    "exit",
    "quit",
]


@lru_cache(maxsize=1)
def _path_executables() -> tuple[str, ...]:
    """Names of executables found on ``$PATH`` (cached for the session)."""
    found: set[str] = set()
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        if not directory or not os.path.isdir(directory):
            continue
        try:
            entries = os.listdir(directory)
        except OSError:
            continue
        for name in entries:
            full = os.path.join(directory, name)
            if os.access(full, os.X_OK) and not os.path.isdir(full):
                found.add(name)
    return tuple(sorted(found))


class CommandCompleter(Completer):
    """Completes the first word against built-ins and ``$PATH`` executables.

    For later words it delegates to a :class:`PathCompleter` so file arguments
    complete too.
    """

    def __init__(self) -> None:
        self._path_completer = PathCompleter(expanduser=True)

    def get_completions(self, document: Document, complete_event):  # noqa: ANN001
        text = document.text_before_cursor
        # First word: complete commands. We treat the cursor as being on the
        # first word when there is no whitespace before it.
        if " " not in text.lstrip() and "\t" not in text:
            word = document.get_word_before_cursor(WORD=True)
            for cmd in BUILTIN_COMMANDS:
                if cmd.startswith(word):
                    yield Completion(cmd, start_position=-len(word))
            for exe in _path_executables():
                if exe.startswith(word) and word:
                    yield Completion(exe, start_position=-len(word))
            return

        # Later words: offer filesystem path completion.
        yield from self._path_completer.get_completions(document, complete_event)


def build_completer(kubectl_live: bool = False) -> Completer:
    """Return the merged completer used by the REPL.

    ``kubectl_live`` enables cluster-aware kubectl completion (opt-in; see
    :class:`~terminal_triage.completion.kubectl.KubectlCompleter`).
    """
    return merge_completers(
        [CommandCompleter(), KubectlCompleter(live=kubectl_live)]
    )
