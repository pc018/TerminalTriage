# CLAUDE.md

Guidance for Claude Code (and other AI assistants) working in this repository.

## What this is

TerminalTriage is an AI-powered interactive troubleshooting terminal. It runs shell
commands and, when analysis mode is on, streams the command + output to an AI provider
(Anthropic / OpenAI / Gemini) for explanation and next-step suggestions.

## Project layout (src layout)

```
src/terminal_triage/
  __init__.py        Version.
  __main__.py        `python -m terminal_triage` entry point.
  cli.py             argparse CLI; builds Settings, launches the REPL. Console script: `triage`.
  config.py          Settings dataclass + load_settings(); provider defaults & API-key env map.
  ui.py              ANSI color constants.
  shell.py           run_command() -> CommandResult (subprocess wrapper).
  prompts.py         build_analysis_prompt() / build_question_prompt().
  terminal.py        TriageTerminal: prompt_toolkit REPL + dispatch (handle_line).
  completion/
    __init__.py      build_completer(): merges builtins + $PATH execs + paths + kubectl.
    kubectl.py       KubectlCompleter: offline static verb/resource/flag tables;
                     opt-in live mode delegates to `kubectl __complete`.
  ai/
    base.py          AIProvider ABC (stream()), ProviderError.
    factory.py       get_provider(settings); lazy imports per provider.
    anthropic_provider.py / openai_provider.py / gemini_provider.py
tests/               pytest suite (mirrors the modules above).
```

## Common commands

```bash
pip install -e '.[all,dev]'    # install with all providers + dev tools
pytest                         # run tests (must stay network-free)
ruff check .                   # lint
ruff format .                  # format
triage                         # run the app
```

This repo's dev environment uses `uv`; create a venv with
`uv venv .venv && uv pip install --python .venv/bin/python -e '.[all,dev]'`.

## Architecture notes

- **Streaming everywhere.** Every provider implements `stream(prompt) -> Iterator[str]`
  and yields text chunks. The terminal prints them as they arrive.
- **Lazy SDK imports.** Each provider imports its vendor SDK inside `__init__`, so a
  missing optional dependency only errors when that provider is actually selected — and
  it raises a `ProviderError` naming the extra to install.
- **Config flow.** `load_settings()` reads env vars (and `.env` via python-dotenv, real
  env wins), resolves the per-provider API key and default model, and returns `Settings`.
- **Dispatch is decoupled from prompt_toolkit.** `TriageTerminal.handle_line()` contains
  all routing logic and is unit-tested directly; `run()` only wires up the interactive
  session (history, completer, Ctrl+A binding).
- **kubectl completion is offline by default, live by opt-in.** `KubectlCompleter` serves
  a static verb/resource/flag grammar with no subprocess calls. With `live=True` (set by
  `--kubectl-live-completion` / `AI_KUBECTL_LIVE_COMPLETION`, threaded through
  `Settings.kubectl_live_completion` -> `build_completer(kubectl_live)`), it delegates to
  `kubectl __complete` for cluster-aware results (CRDs, namespace/pod names), with a short
  timeout and a transparent fallback to the static grammar on any failure. The subprocess
  runner is injectable so tests stay offline.

## Conventions

- **Tests never hit the network.** Inject a fake provider (see `tests/conftest.py`'s
  `FakeProvider`) instead of constructing real ones.
- **Adding a provider:** subclass `AIProvider` in `ai/<name>_provider.py` with a lazy
  SDK import, register it in `ai/factory.py::_PROVIDERS`, add its default model and
  API-key env var in `config.py`, and add a `pyproject.toml` extra.
- **Extending completion:** add static tables to `completion/kubectl.py` or a sibling
  module and merge it in `completion/__init__.py::build_completer`. Keep the offline
  static path working even when a live (subprocess-backed) path exists — it's the default
  and the fallback, and it's what keeps tests network-free.
- Keep line length ≤ 100 (ruff config in `pyproject.toml`).
