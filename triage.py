import cmd
import subprocess
import os
import shlex
from anthropic import Anthropic

# ANSI Colors for UI
CYAN = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'

class KubeTerminal(cmd.Cmd):
    intro = f"{BOLD}Welcome to the K8s + Claude Terminal.{RESET}\nType 'help' or '?' to list commands.\n"
    prompt = f"{CYAN}(k8s){RESET} "
    
    def __init__(self):
        super().__init__()
        self.claude_mode = False
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = None
        
        # Initialize Anthropic client if key exists
        if self.api_key:
            try:
                self.client = Anthropic(api_key=self.api_key)
            except Exception as e:
                print(f"{RED}Error initializing Claude: {e}{RESET}")
        else:
            print(f"{YELLOW}Warning: ANTHROPIC_API_KEY not found. Claude mode will be disabled.{RESET}")

    def do_claude(self, arg):
        """Toggle Claude Code analysis mode on/off.
        Usage: claude [on|off]"""
        if not self.client:
            print(f"{RED}Cannot turn on Claude: No API Key set.{RESET}")
            return

        if arg.lower() == 'on':
            self.claude_mode = True
            self.prompt = f"{CYAN}(k8s){YELLOW} 🤖 {RESET} "
            print(f"{GREEN}Claude Code Analysis: ENABLED{RESET}")
        elif arg.lower() == 'off':
            self.claude_mode = False
            self.prompt = f"{CYAN}(k8s){RESET} "
            print(f"{YELLOW}Claude Code Analysis: DISABLED{RESET}")
        else:
            print("Usage: claude [on|off]")

    def default(self, line):
        """Run a shell command (default behavior)."""
        # Prevent running forbidden or dangerous interactive commands if needed
        if line in ['quit', 'exit']:
            return True
        
        try:
            # 1. Execute the command locally
            args = shlex.split(line)
            result = subprocess.run(
                args, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            # Print the standard output/error to the user
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(f"{RED}{result.stderr}{RESET}")

            # 2. If Claude Mode is ON, send context to AI
            if self.claude_mode:
                self._analyze_with_claude(line, result.stdout, result.stderr)

        except FileNotFoundError:
            print(f"{RED}Command not found: {args[0]}{RESET}")
        except Exception as e:
            print(f"{RED}Execution Error: {e}{RESET}")

    def _analyze_with_claude(self, command, stdout, stderr):
        """Sends the command output to Claude for insights using Streaming."""
        print(f"\n{YELLOW}--- 🧠 Claude is analyzing ---{RESET}")
        
        # Construct the prompt context
        user_message = f"""
        I am running a Kubernetes management terminal.
        I just ran this command: `{command}`
        
        STDOUT:
        {stdout[:2000]}
        
        STDERR:
        {stderr[:2000]}
        
        If there is an error, explain how to fix it.
        If the output is successful, briefly summarize the status of the cluster resources.
        Provide a specific next 'kubectl' command if applicable.
        """

        try:
            # We use the stream() context manager to handle the response chunk-by-chunk
            # This satisfies the "Streaming is required" constraint
            with self.client.messages.stream(
                model="claude-sonnet-4-6", # Use the stable alias
                max_tokens=50000,
                messages=[{"role": "user", "content": user_message}]
            ) as stream:
                print(f"{CYAN}", end="", flush=True) # Start Color
                for text in stream.text_stream:
                    print(text, end="", flush=True)
                print(f"{RESET}\n") # End Color & Newline

        except Exception as e:
            print(f"{RED}Claude API Error: {e}{RESET}")

if __name__ == '__main__':
    try:
        KubeTerminal().cmdloop()
    except KeyboardInterrupt:
        print("\nExiting...")
