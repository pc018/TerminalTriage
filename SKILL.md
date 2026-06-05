---
name: terminal-triage
description: Troubleshoot a failing shell/kubectl/Docker command using the TerminalTriage AI terminal. Use when a command errored and you want an AI explanation and suggested fix, or to ask free-form ops questions, with streaming analysis from Anthropic, OpenAI, or Gemini.
---

# TerminalTriage skill

Drive the TerminalTriage terminal to diagnose failing commands and answer
troubleshooting questions.

## When to use

- A shell, `kubectl`, or `docker` command failed and you want the cause + a fix.
- You want a quick, command-oriented answer to an ops/devops question.
- You want each command's output automatically explained while you work.

## Setup

1. Install with a provider (once): `pip install -e '.[anthropic]'` (or `.[openai]` /
   `.[gemini]` / `.[all]`).
2. Configure `.env` (copy from `.env.example`):
   - `AI_PROVIDER=anthropic|openai|gemini`
   - the matching API key (`ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GEMINI_API_KEY`)
   - optional `AI_MODEL`.
3. Launch: `triage` (or `python -m terminal_triage`). Add `--analyze` to start with
   analysis already on, or `--provider <name>` to override.

## Workflow

1. **Enable analysis:** type `claude on` to auto-explain command output, or leave it off
   and explain on demand.
2. **Reproduce the problem:** run the command as you normally would, e.g.
   `kubectl get pods -n prod`. Tab completes kubectl verbs, resources, and flags.
3. **Read the streamed analysis:** when analysis mode is on, the AI prints an
   explanation and a suggested next command right after the output.
4. **Ask follow-ups:** `/ai why is this pod CrashLoopBackOff?` for a free-form question,
   or press **Ctrl+A** to open a one-off side prompt without disturbing your command line.
5. **Iterate:** apply the suggested command, rerun, and repeat. `exit` or `quit` to leave.

## Tips

- Switch providers by changing `AI_PROVIDER` (or `triage --provider <name>`); each uses
  a sensible default model unless `AI_MODEL` is set.
- Analysis is streamed and capped to a few thousand characters of command output, so
  large logs are truncated before being sent.
