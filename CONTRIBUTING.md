# Contributing

Thanks for your interest in improving TerminalTriage!

## Development setup

```bash
git clone https://github.com/pc018/TerminalTriage.git
cd TerminalTriage
pip install -e '.[all,dev]'
```

(Or, with [uv](https://docs.astral.sh/uv/):
`uv venv .venv && uv pip install --python .venv/bin/python -e '.[all,dev]'`.)

## Running checks

```bash
pytest            # test suite — must stay network-free
ruff check .      # lint
ruff format .     # auto-format
```

All tests must pass and the linter must be clean before opening a pull request.

## Guidelines

- **No network in tests.** Inject the `FakeProvider` from `tests/conftest.py` instead of
  constructing real AI clients.
- **Match the existing style.** Keep lines ≤ 100 characters; ruff enforces import order
  and common lints (see `pyproject.toml`).
- **Adding an AI provider:** subclass `AIProvider` (`src/terminal_triage/ai/`) with a
  lazy SDK import, register it in `ai/factory.py`, add its default model + API-key env
  var in `config.py`, and add a `pyproject.toml` extra. See [CLAUDE.md](CLAUDE.md).
- **Document user-facing changes** in the README.

## Reporting issues

Please include the command you ran, the provider/model, and the full output (with secrets
redacted).
