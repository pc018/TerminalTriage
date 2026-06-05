"""The interactive TerminalTriage REPL (prompt_toolkit)."""

from __future__ import annotations

from collections.abc import Callable

from .ai import AIProvider, get_provider
from .ai.base import ProviderError
from .config import Settings
from .prompts import build_analysis_prompt, build_question_prompt
from .shell import run_command
from .ui import BOLD, CYAN, GREEN, RED, RESET, YELLOW

HELP_TEXT = f"""{BOLD}TerminalTriage commands{RESET}
  <any shell command>   Run it locally (e.g. `kubectl get pods`, `ls -la`).
  claude on | off       Toggle proactive AI analysis of command output.
  /ai <question>        Ask the AI a free-form question.
  help                  Show this help.
  exit | quit           Leave the terminal.

  Ctrl+A                Open a one-off AI side prompt.
"""


class TriageTerminal:
    """Dispatches user input to the shell or the AI provider.

    The dispatch logic (:meth:`handle_line`) is independent of prompt_toolkit so
    it can be unit-tested directly. :meth:`run` wires up the interactive session.
    """

    def __init__(
        self,
        settings: Settings,
        provider: AIProvider | None = None,
        output: Callable[..., None] = print,
    ) -> None:
        self.settings = settings
        self.output = output
        self._provider = provider
        self._provider_attempted = provider is not None
        self.analysis_mode = settings.auto_analyze

    # -- provider management ------------------------------------------------

    def get_provider(self) -> AIProvider | None:
        """Return the AI provider, constructing it on first use.

        Prints a friendly error and returns ``None`` if it cannot be created.
        """
        if self._provider is not None:
            return self._provider
        if self._provider_attempted:
            return None
        self._provider_attempted = True
        try:
            self._provider = get_provider(self.settings)
        except ProviderError as exc:
            self.output(f"{RED}{exc}{RESET}")
            return None
        return self._provider

    # -- streaming helper ---------------------------------------------------

    def _stream(self, prompt: str) -> None:
        provider = self.get_provider()
        if provider is None:
            return
        self.output(f"\n{YELLOW}--- 🧠 {provider.name} is analyzing ---{RESET}")
        try:
            self.output(CYAN, end="", flush=True)
            for chunk in provider.stream(prompt):
                self.output(chunk, end="", flush=True)
            self.output(f"{RESET}\n")
        except ProviderError as exc:
            self.output(f"{RESET}\n{RED}{exc}{RESET}")

    # -- dispatch -----------------------------------------------------------

    def handle_line(self, line: str) -> bool:
        """Process one input line. Return ``True`` to exit the loop."""
        line = line.strip()
        if not line:
            return False

        if line in ("exit", "quit"):
            return True

        if line == "help" or line == "?":
            self.output(HELP_TEXT)
            return False

        if line == "claude" or line.startswith("claude "):
            self._handle_claude(line[len("claude"):].strip())
            return False

        if line == "/ai" or line.startswith("/ai "):
            question = line[len("/ai"):].strip()
            self._handle_ai(question)
            return False

        self._handle_shell(line)
        return False

    def _handle_claude(self, arg: str) -> None:
        arg = arg.lower()
        if arg == "on":
            if self.get_provider() is None:
                return
            self.analysis_mode = True
            self.output(f"{GREEN}AI analysis: ENABLED{RESET}")
        elif arg == "off":
            self.analysis_mode = False
            self.output(f"{YELLOW}AI analysis: DISABLED{RESET}")
        else:
            self.output("Usage: claude [on|off]")

    def _handle_ai(self, question: str) -> None:
        if not question:
            self.output("Usage: /ai <question>")
            return
        self._stream(build_question_prompt(question))

    def _handle_shell(self, line: str) -> None:
        result = run_command(line)
        if result.error:
            self.output(f"{RED}{result.error}{RESET}")
        if result.stdout:
            self.output(result.stdout)
        if result.stderr:
            self.output(f"{RED}{result.stderr}{RESET}")

        if self.analysis_mode:
            self._stream(
                build_analysis_prompt(result.command, result.stdout, result.stderr)
            )

    # -- interactive session ------------------------------------------------

    def run(self) -> None:
        """Run the interactive prompt_toolkit loop."""
        from prompt_toolkit import PromptSession
        from prompt_toolkit.history import FileHistory
        from prompt_toolkit.patch_stdout import patch_stdout

        from .completion import build_completer

        self.settings.history_file.parent.mkdir(parents=True, exist_ok=True)
        session: PromptSession = PromptSession(
            history=FileHistory(str(self.settings.history_file)),
            completer=build_completer(),
            complete_while_typing=False,
            key_bindings=self._key_bindings(),
        )

        self.output(
            f"{BOLD}Welcome to TerminalTriage.{RESET}\n"
            f"Provider: {self.settings.provider} ({self.settings.model}). "
            "Type 'help' for commands.\n"
        )

        while True:
            try:
                with patch_stdout():
                    line = session.prompt(self._prompt_text())
            except KeyboardInterrupt:
                continue  # Ctrl+C clears the current line.
            except EOFError:
                break  # Ctrl+D exits.
            if self.handle_line(line):
                break
        self.output("Exiting...")

    def _prompt_text(self) -> str:
        from prompt_toolkit.formatted_text import ANSI

        marker = " 🤖" if self.analysis_mode else ""
        return ANSI(f"{CYAN}(triage){marker}{RESET} ")

    def _key_bindings(self):
        from prompt_toolkit.key_binding import KeyBindings

        kb = KeyBindings()

        @kb.add("c-a")
        def _(event) -> None:  # noqa: ANN001
            """Ctrl+A: open a one-off AI side prompt."""
            def ask() -> None:
                from prompt_toolkit import prompt as ptk_prompt

                try:
                    question = ptk_prompt("ai> ")
                except (EOFError, KeyboardInterrupt):
                    return
                if question.strip():
                    self._handle_ai(question.strip())

            event.app.run_in_terminal(ask)

        return kb
