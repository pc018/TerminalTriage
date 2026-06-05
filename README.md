# AI-Powered Python Terminal for Troubleshooting

A Python-based interactive terminal with an integrated AI backend that runs silently in the background, providing real-time assistance and troubleshooting support.

## Overview

This tool combines a familiar command-line interface with the intelligence of an AI model. As you type commands or encounter errors, the AI analyzes the context and suggests fixes, explains issues, or recommends next steps—without interrupting your workflow.

## Features

- **Native Python terminal** with command history and auto-completion
- **Background AI engine** that monitors session activity
- **Proactive troubleshooting** – detects errors and suggests solutions
- **Natural language queries** – ask the AI for help using plain English
- **Low latency** – AI runs locally or via a lightweight API
- **Extensible** – easily add custom troubleshooting rules or connect to different AI providers

## Installation

```bash
git clone https://github.com/pc018/TerminalTriage.git
cd TerminalTriage
pip install -r requirements.txt

Usage

Start the terminal with:
python triage

Once inside, use the terminal as you normally would. The AI will listen in the background and offer assistance when needed. To explicitly ask for help, type:
text

/ai What does this error mean?

Or simply press Ctrl + A to open a side prompt for AI queries.

Configuration

Create a .env file to set your AI provider and API key (optional if using a local model):
text

AI_PROVIDER=openai
OPENAI_API_KEY=your_key_here
AI_MODEL=gpt-3.5-turbo

Requirements

    Python 3.13+

    Dependencies listed in requirements.txt

Contributing

Pull requests and issue reports are welcome. Please ensure your code passes existing tests and includes appropriate documentation.
License

MIT
Acknowledgements

Built for system administrators, developers, and anyone who spends hours debugging in the terminal.
