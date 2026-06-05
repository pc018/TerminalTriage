"""The interactive TerminalTriage REPL (prompt_toolkit)."""

from __future__ import annotations

import os
from collections.abc import Callable

from .ai import AIProvider, get_provider
from .ai.base import ProviderError
from .config import API_KEY_ENV, DEFAULT_MODELS, Settings
from .prompts import build_analysis_prompt, build_question_prompt
from .shell import CommandResult, run_command
from .ui import BOLD, CYAN, GREEN, RED, RESET, YELLOW

# Provider-switch command -> provider name understood by the factory/config.
PROVIDER_COMMANDS: dict[str, str] = {
    "/claude": "anthropic",
    "/openai": "openai",
    "/gemini": "gemini",
}

HELP_TEXT = f"""{BOLD}TerminalTriage commands{RESET}
  <any shell command>   Run it locally (e.g. `kubectl get pods`, `ls -la`).
  ai on | off           Toggle proactive AI analysis of command output.
  /ai <question>        Ask the AI a free-form question.
  /claude               Switch the AI provider to Anthropic (Claude).
  /openai               Switch the AI provider to OpenAI.
  /gemini               Switch the AI provider to Google Gemini.
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
        self._last_result: CommandResult | None = None

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

        if line == "ai" or line.startswith("ai "):
            self._handle_ai_toggle(line[len("ai") :].strip())
            return False

        command = line.split(maxsplit=1)[0]
        if command in PROVIDER_COMMANDS:
            self._handle_switch_provider(PROVIDER_COMMANDS[command])
            return False

        if line == "/ai" or line.startswith("/ai "):
            question = line[len("/ai") :].strip()
            self._handle_ai(question)
            return False

        self._handle_shell(line)
        return False

    def _handle_ai_toggle(self, arg: str) -> None:
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
            self.output("Usage: ai [on|off]")

    def _handle_switch_provider(self, provider: str) -> None:
        """Switch the active AI provider, re-resolving its API key and model."""
        previous = (
            self.settings.provider,
            self.settings.api_key,
            self.settings.model,
            self._provider,
            self._provider_attempted,
        )

        self.settings.provider = provider
        key_env = API_KEY_ENV.get(provider)
        self.settings.api_key = os.getenv(key_env) if key_env else None
        self.settings.model = DEFAULT_MODELS.get(provider, "")

        # Force the provider to be rebuilt on next use.
        self._provider = None
        self._provider_attempted = False

        if self.get_provider() is None:
            # Could not build the new provider; restore the previous one.
            (
                self.settings.provider,
                self.settings.api_key,
                self.settings.model,
                self._provider,
                self._provider_attempted,
            ) = previous
            return

        self.output(
            f"{GREEN}AI provider: {self.settings.provider} "
            f"({self.settings.model}){RESET}"
        )

    def _handle_ai(self, question: str) -> None:
        if not question:
            self.output("Usage: /ai <question>")
            return
        result = self._last_result
        if result is None:
            prompt = build_question_prompt(question)
        else:
            prompt = build_question_prompt(
                question,
                command=result.command,
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
            )
        self._stream(prompt)

    def _handle_shell(self, line: str) -> None:
        result = run_command(line)
        self._last_result = result
        if result.error:
            self.output(f"{RED}{result.error}{RESET}")
        if result.stdout:
            self.output(result.stdout)
        if result.stderr:
            self.output(f"{RED}{result.stderr}{RESET}")

        if self.analysis_mode:
            self._stream(
                build_analysis_prompt(
                    result.command,
                    result.stdout,
                    result.stderr,
                    result.returncode,
                )
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
            completer=build_completer(self.settings.kubectl_live_completion),
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
        async def _(event) -> None:  # noqa: ANN001
            """Ctrl+A: open a one-off AI side prompt."""
            from prompt_toolkit.application import in_terminal

            async with in_terminal():
                question = await self._ask_side_prompt()
                if question:
                    self._handle_ai(question)

        return kb

    async def _ask_side_prompt(self) -> str:
        """Read a one-off question from a nested prompt; '' if cancelled/blank."""
        from prompt_toolkit import PromptSession

        try:
            question = await PromptSession().prompt_async("ai> ")
        except (EOFError, KeyboardInterrupt):
            return ""
        return question.strip()
