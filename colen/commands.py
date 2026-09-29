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
        ("tools", "Show available automation tools and their status"),
        ("audit", "Show recent tool execution audit log"),
        ("exit, q", "Exit Colen"),
        ("<any question>", "Ask Colen anything (instant voice reply via Groq + PocketTTS + automation tools)"),
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


def show_tools_help() -> None:
    """Display available automation tools and their status."""
    try:
        from colen.config import get_config
        config = get_config()
    except ImportError:
        console.print("[dim]Tools module not available. Install dependencies to enable automation features.[/dim]")
        return
    
    tools_text = Text()
    tools_text.append("Available Automation Tools, Sir:\n\n", style="bold cyan")
    
    # Tool categories and their status
    tool_categories = [
        ("File Operations", config.ENABLE_FILE_OPERATIONS, [
            "create_folder - Create new folders",
            "delete_file - Delete files",
            "delete_folder - Delete folders",
            "write_file - Write content to files",
            "read_file - Read file contents",
            "list_directory - List directory contents",
            "copy_file - Copy files",
            "move_file - Move files",
        ]),
        ("Application Management", config.ENABLE_APP_OPERATIONS, [
            "open_application - Launch applications",
            "open_file_with_app - Open files with apps",
            "find_window - Find windows by title",
            "focus_window - Focus windows",
            "minimize_window - Minimize windows",
            "maximize_window - Maximize windows",
            "close_window - Close windows",
            "list_windows - List all windows",
            "move_window - Move windows",
            "resize_window - Resize windows",
        ]),
        ("Shell Commands", config.ENABLE_SHELL_COMMANDS, [
            "execute_command - Run shell commands",
            "execute_powershell - Run PowerShell commands",
            "get_environment_variable - Get environment variables",
            "set_environment_variable - Set environment variables",
            "list_processes - List running processes",
            "kill_process - Kill processes",
        ]),
        ("Content Generation", config.ENABLE_CONTENT_GENERATION, [
            "generate_prompt - Generate prompts",
            "write_prompt_to_file - Write prompts to files",
            "generate_code_snippet - Generate code snippets",
            "generate_documentation - Generate documentation",
        ]),
    ]
    
    for category, enabled, tools in tool_categories:
        status = "[green]+ Enabled[/green]" if enabled else "[red]- Disabled[/red]"
        tools_text.append(f"  {category}: {status}\n", style="bold yellow")
        if enabled:
            for tool in tools:
                tools_text.append(f"    - {tool}\n", style="dim")
        tools_text.append("\n")
    
    # Safety settings
    tools_text.append("Safety Settings:\n", style="bold yellow")
    tools_text.append(f"  Confirmation Mode: [cyan]{config.CONFIRMATION_MODE}[/cyan]\n")
    tools_text.append(f"  Tools Enabled: [cyan]{config.ENABLE_TOOLS}[/cyan]\n")
    tools_text.append(f"  Max File Size: [cyan]{config.MAX_FILE_SIZE_MB}MB[/cyan]\n")
    tools_text.append(f"  Command Timeout: [cyan]{config.MAX_COMMAND_TIMEOUT}s[/cyan]\n")
    
    panel = Panel(tools_text, title="[bold]Automation Tools[/bold]", border_style="cyan", padding=(1, 2))
    console.print(panel)


def show_audit_log() -> None:
    """Display recent tool execution audit log."""
    try:
        from colen.tools.audit import get_audit_logger
        logger = get_audit_logger()
        recent_ops = logger.get_recent_operations(10)
        stats = logger.get_operation_statistics()
    except ImportError:
        console.print("[dim]Audit module not available. Install dependencies to enable audit logging.[/dim]")
        return
    except Exception as e:
        console.print(f"[dim]Error reading audit log: {e}[/dim]")
        return
    
    audit_text = Text()
    audit_text.append("Tool Execution Audit Log, Sir:\n\n", style="bold cyan")
    
    # Statistics
    audit_text.append(f"Total Operations: [bold yellow]{stats['total']}[/bold yellow]\n")
    audit_text.append(f"Successful: [green]+ {stats['successful']}[/green]\n")
    audit_text.append(f"Failed: [red]- {stats['failed']}[/red]\n\n")
    
    if stats['by_operation']:
        audit_text.append("Operations by Type:\n", style="bold yellow")
        for op, count in sorted(stats['by_operation'].items(), key=lambda x: x[1], reverse=True):
            audit_text.append(f"  {op}: [cyan]{count}[/cyan]\n")
        audit_text.append("\n")
    
    # Recent operations
    if recent_ops:
        audit_text.append("Recent Operations:\n", style="bold yellow")
        for op in recent_ops[-5:]:  # Show last 5
            timestamp = op.get('timestamp', 'N/A')[:19]  # Truncate microseconds
            operation = op.get('operation', 'unknown')
            success = "[green]+[/green]" if op.get('success') else "[red]-[/red]"
            audit_text.append(f"  {timestamp} | {operation} | {success}\n")
    else:
        audit_text.append("[dim]No recent operations logged.[/dim]\n")
    
    panel = Panel(audit_text, title="[bold]Audit Log[/bold]", border_style="cyan", padding=(1, 2))
    console.print(panel)