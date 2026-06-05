# AI-Powered Python Terminal for Troubleshooting

TerminalTriage is an interactive terminal with an integrated AI backend. You use it
like a normal shell; when analysis mode is on, each command and its output are streamed
to an AI model that explains errors, summarizes results, and suggests the next step.

## Overview

This tool combines a familiar command-line interface with the intelligence of an AI
model. Run commands as usual — and when something fails, the AI analyzes the context and
suggests fixes, explains the issue, or recommends what to try next. You can also ask it
free-form questions without leaving the terminal.

## Features

- **Interactive terminal** with persistent command history and auto-completion
  (built on [prompt_toolkit](https://python-prompt-toolkit.readthedocs.io/)).
- **kubectl-aware completion** for verbs, resource types, and common flags — offline
  by default, with opt-in live completion that delegates to `kubectl __complete` for
  cluster-aware suggestions (CRDs, real namespace/pod names).
- **Streaming AI analysis** – the response prints as it arrives.
- **Multiple providers** – Anthropic Claude, OpenAI, or Google Gemini, selectable via
  configuration.
- **Proactive troubleshooting** – toggle analysis mode to auto-explain command output.
- **Natural-language queries** – ask the AI for help with `/ai <question>`.
- **Ctrl+A side prompt** – pop open a one-off AI question at any time.

## Installation

```bash
git clone https://github.com/pc018/TerminalTriage.git
cd TerminalTriage

# Install with all AI providers:
pip install -e '.[all]'

# ...or install just the one you use:
pip install -e '.[anthropic]'   # or .[openai] / .[gemini]
```

Requires Python 3.10+.

## Configuration

Copy `.env.example` to `.env` and fill in the provider you want to use:

```ini
# Which provider: anthropic | openai | gemini
AI_PROVIDER=anthropic

# Only the matching key is required:
ANTHROPIC_API_KEY=your_key_here
# OPENAI_API_KEY=your_key_here
# GEMINI_API_KEY=your_key_here

# Optional overrides:
# AI_MODEL=claude-sonnet-4-6
# AI_MAX_TOKENS=4096

# Live kubectl completion (talks to the cluster). Off by default:
# AI_KUBECTL_LIVE_COMPLETION=1
```

Real environment variables take precedence over `.env`. If `AI_MODEL` is unset, a
sensible default is chosen per provider (`claude-sonnet-4-6`, `gpt-4o-mini`,
`gemini-2.0-flash`).

### kubectl completion

By default, kubectl tab-completion is fully offline, served from a built-in static
grammar of verbs, resource types, and flags. To get authoritative, cluster-aware
suggestions — every subcommand, custom resources (CRDs), and dynamic values such as
real namespace and pod names — enable **live completion**, which delegates to
`kubectl __complete` (the engine behind `kubectl completion bash|zsh`):

```bash
triage --kubectl-live-completion        # or set AI_KUBECTL_LIVE_COMPLETION=1
```

This is opt-in because it runs `kubectl` (and thus contacts the cluster) as you type.
Calls are capped by a short timeout, and if `kubectl` is unavailable or the call fails
it transparently falls back to the offline grammar.

## Usage

Start the terminal:

```bash
triage
# or, equivalently:
python -m terminal_triage
```

Useful flags: `triage --provider openai`, `triage --model gpt-4o`, `triage --analyze`,
`triage --kubectl-live-completion`.

Once inside, use it like a normal shell. Commands:

| Command            | Action                                            |
| ------------------ | ------------------------------------------------- |
| `<shell command>`  | Run it locally (e.g. `kubectl get pods`, `ls`).   |
| `claude on` / `off`| Toggle proactive AI analysis of command output.   |
| `/ai <question>`   | Ask the AI a free-form question.                  |
| `help`             | List commands.                                    |
| `exit` / `quit`    | Leave the terminal.                               |
| `Ctrl+A`           | Open a one-off AI side prompt.                    |

Example:

```text
(triage) claude on
AI analysis: ENABLED
(triage) 🤖 kubectl get pods
... command output ...
--- 🧠 anthropic is analyzing ---
The error indicates no cluster is configured. Run `kubectl config ...`
```

## Development

```bash
pip install -e '.[all,dev]'
pytest            # run the test suite (no network calls)
ruff check .      # lint
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for more, and [CLAUDE.md](CLAUDE.md) for an
architecture overview.

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgements

Built for system administrators, developers, and anyone who spends hours debugging in
the terminal.
