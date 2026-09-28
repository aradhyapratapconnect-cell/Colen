"""Command implementations for Colen CLI."""

import platform
import sys
from datetime import datetime
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def show_system_info() -> None:
    """Display system information."""
    table = Table(title="System Information", show_header=True, header_style="bold cyan")
    table.add_column("Property", style="yellow")
    table.add_column("Value", style="green")

    table.add_row("OS", f"{platform.system()} {platform.release()}")
    table.add_row("Architecture", platform.machine())
    table.add_row("Processor", platform.processor())
    table.add_row("Python Version", sys.version.split()[0])
    table.add_row("Platform", platform.platform())
    table.add_row("Current Time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    console.print(table)


def show_help_panel() -> None:
    """Display available commands in a beautiful panel."""
    help_text = Text()
    help_text.append("Available Commands, Sir:\n\n", style="bold cyan")
    
    commands = [
        ("help, h", "Show this help message"),
        ("info, i", "Show system information"),
        ("time, t", "Show current date and time"),
        ("banner, b", "Show the Colen banner"),
        ("clear, c", "Clear the terminal / conversation context"),
        ("exit, q", "Exit Colen"),
        ("<any question>", "Ask Colen anything (instant voice reply via Groq + PocketTTS)"),
    ]
    
    for cmd, desc in commands:
        help_text.append(f"  {cmd:<18} ", style="bold yellow")
        help_text.append(f"{desc}\n", style="white")
    
    panel = Panel(help_text, title="[bold]Colen Commands[/bold]", border_style="cyan", padding=(1, 2))
    console.print(panel)


def show_time() -> None:
    """Display current date and time."""
    now = datetime.now()
    time_text = Text()
    time_text.append("Current Time: ", style="bold cyan")
    time_text.append(now.strftime("%A, %B %d, %Y"), style="bold yellow")
    time_text.append("\n")
    time_text.append("Time: ", style="bold cyan")
    time_text.append(now.strftime("%H:%M:%S"), style="bold green")
    time_text.append(f" ({now.strftime('%Z')})", style="dim")
    
    panel = Panel(time_text, title="[bold]Time[/bold]", border_style="yellow", padding=(1, 2))
    console.print(panel)


def show_banner(style: str = "default") -> None:
    """Display the Colen banner."""
    from colen.art import BANNERS
    
    banner_func = BANNERS.get(style, BANNERS["default"])
    banner = banner_func()
    
    console.print(banner, style="bold cyan")


def clear_terminal() -> None:
    """Clear the terminal screen."""
    click.clear()
    show_banner("minimal")
    console.print("[dim]Terminal cleared. Welcome back, Sir.[/dim]\n")


def handle_unknown_command(command: str) -> None:
    """Handle unknown commands."""
    console.print(f"[red]Unknown command:[/red] [yellow]{command}[/yellow]")
    console.print("[dim]Type 'help' for available commands, Sir.[/dim]\n")