"""Main CLI interface for Colen."""

import sys
import time
import threading
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from colen.art import BANNERS
from colen.commands import (
    clear_terminal,
    handle_unknown_command,
    show_banner,
    show_help_panel,
    show_system_info,
    show_time,
    show_tools_help,
    show_audit_log,
)

console = Console()


def type_text(text: str, style: str = "bold cyan", delay: float = 0.008) -> None:
    """Type out text character by character with a typing effect."""
    for char in text:
        console.print(char, style=style, end="", soft_wrap=True)
        sys.stdout.flush()
        time.sleep(delay)
    console.print()


def startup_sequence() -> None:
    """Display the startup initialization sequence (kept snappy)."""
    console.print()
    type_text("[ Initializing Colen...", style="bold cyan", delay=0.005)
    time.sleep(0.05)
    type_text("[ Loading core modules...", style="cyan", delay=0.005)
    time.sleep(0.03)
    type_text("[ Establishing neural pathways...", style="cyan", delay=0.005)
    time.sleep(0.03)
    type_text("[ Calibrating interface...", style="cyan", delay=0.005)
    time.sleep(0.05)
    type_text("[ System online.", style="bold green", delay=0.008)
    time.sleep(0.05)
    console.print()


def print_welcome() -> None:
    """Print the welcome message."""
    show_banner("jarvis")
    
    welcome_text = Text()
    welcome_text.append("Good evening, Sir. ", style="bold white")
    welcome_text.append("Colen", style="bold cyan")
    welcome_text.append(" at your service.\n", style="bold white")
    welcome_text.append("Ask me anything directly, or type ", style="dim")
    welcome_text.append("help", style="bold yellow")
    welcome_text.append(" for built-in commands.", style="dim")
    
    panel = Panel(welcome_text, border_style="cyan", padding=(1, 2))
    console.print(panel)
    console.print()

    # Speak the startup greeting aloud via PocketTTS (best-effort).  Runs in a
    # background thread so the shell stays responsive; never breaks startup if
    # the speech module / server / voice reference is unavailable.
    _start_speech_greeting()


def _start_speech_greeting() -> None:
    """Synthesise and play the Colen startup greeting (non-blocking)."""
    greeting = "Good evening, Sir. Colen at your service."
    try:
        from colen.speech import speak  # lazy import keeps the CLI light
    except Exception as exc:  # pragma: no cover - speech is optional
        console.print(f"[dim](speech unavailable: {type(exc).__name__})[/dim]")
        return

    def _speak() -> None:
        try:
            speak(greeting, play=True)
        except Exception as exc:  # pragma: no cover - never crash the shell
            console.print(f"[dim](speech error: {type(exc).__name__})[/dim]")

    threading.Thread(target=_speak, daemon=True).start()


def _speak_exit_greeting(text: str = "Goodbye, Sir. Have a pleasant day.") -> None:
    """Speak the Colen exit greeting aloud (blocking, so it is fully heard).

    This deliberately runs in the *calling* thread: a daemon thread would be
    killed the instant the process exits, so the farewell would never be
    heard.  Blocking here guarantees the goodbye is spoken before Colen quits.
    """
    try:
        from colen.speech import speak  # lazy import keeps the CLI light
    except Exception:
        return

    try:
        speak(text, play=True)  # blocks until the farewell has finished
    except Exception as exc:
        console.print(f"[dim](speech error: {type(exc).__name__})[/dim]")


# Shared conversation history across commands in interactive session
_CONVERSATION_HISTORY: list = []


def get_conversation_history() -> list:
    """Return the active conversation history."""
    return _CONVERSATION_HISTORY


def clear_conversation_history() -> None:
    """Clear conversation history."""
    _CONVERSATION_HISTORY.clear()


def process_command(command: str) -> bool:
    """
    Process a user command.
    
    Returns:
        True if should continue, False if should exit.
    """
    cmd = command.strip().lower()
    
    if not cmd:
        return True
    
    # Exit commands
    if cmd in ("exit", "quit", "q", "bye"):
        console.print("[bold cyan]Goodbye, Sir. Have a pleasant day.[/bold cyan]")
        _speak_exit_greeting()
        return False
    
    # Help commands
    if cmd in ("help", "h", "?"):
        show_help_panel()
        return True
    
    # Info commands
    if cmd in ("info", "i", "sysinfo", "system"):
        show_system_info()
        return True
    
    # Time commands
    if cmd in ("time", "t", "date", "datetime"):
        show_time()
        return True
    
    # Banner commands
    if cmd in ("banner", "b"):
        show_banner("default")
        return True
    
    if cmd.startswith("banner "):
        style = cmd.split(" ", 1)[1]
        if style in BANNERS:
            show_banner(style)
        else:
            console.print(f"[red]Unknown banner style:[/red] {style}")
            console.print(f"[dim]Available: {', '.join(BANNERS.keys())}[/dim]")
        return True
    
    # Clear commands
    if cmd in ("clear", "c", "cls", "reset"):
        clear_terminal()
        clear_conversation_history()
        return True
    
    # Tools commands
    if cmd in ("tools", "automation"):
        show_tools_help()
        return True
    
    # Audit commands
    if cmd in ("audit", "log"):
        show_audit_log()
        return True
    
    # Any other prompt: directly talk to Colen using Groq LLM + PocketTTS with tool calling!
    try:
        from colen.assistant import answer
        from colen.config import get_config
        
        config = get_config()
        reply = answer(command, history=_CONVERSATION_HISTORY, play=True, use_tools=config.ENABLE_TOOLS)
        
        # Always manage history in CLI for consistency
        _CONVERSATION_HISTORY.append({"role": "user", "content": command})
        _CONVERSATION_HISTORY.append({"role": "assistant", "content": reply})
        del _CONVERSATION_HISTORY[:-10]  # keep sliding window of context
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
    return True


def run_interactive() -> None:
    """Run the interactive Colen shell."""
    startup_sequence()
    print_welcome()
    
    while True:
        try:
            # Custom prompt with Colen branding
            prompt_text = Text()
            prompt_text.append("[", style="bold cyan")
            prompt_text.append("Colen", style="bold white")
            prompt_text.append("] › ", style="bold cyan")
            
            command = Prompt.ask(prompt_text, console=console)
            
            if not process_command(command):
                break
                
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Interrupted. Type 'exit' to quit, Sir.[/bold yellow]")
        except EOFError:
            console.print("\n[bold cyan]Goodbye, Sir.[/bold cyan]")
            _speak_exit_greeting("Goodbye, Sir.")
            break
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")


@click.command()
@click.option("--interactive", "-i", is_flag=True, help="Run in interactive mode")
@click.option("--banner", "-b", type=click.Choice(list(BANNERS.keys())), default="jarvis", help="Banner style to show")
@click.option("--command", "-c", help="Execute a single command and exit")
@click.version_option(version="0.1.0", prog_name="Colen")
def main(interactive: bool, banner: str, command: Optional[str]) -> None:
    """
    Colen - A beautiful Jarvis-like CLI assistant.
    
    Run without arguments for interactive mode, or use --command to execute a single command.
    """
    if command:
        # Execute single command
        show_banner(banner)
        process_command(command)
        return
    
    if interactive or not sys.stdin.isatty():
        # Force interactive mode
        run_interactive()
    else:
        # Default: show banner and enter interactive mode
        run_interactive()


if __name__ == "__main__":
    main()