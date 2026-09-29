"""Colen Tools - System automation capabilities for the assistant.

This module provides safe, validated tools for file operations, application
management, shell command execution, window control, and content generation.
All tools include comprehensive safety checks and smart confirmation logic.
"""

from colen.tools.file_tools import (
    create_folder,
    delete_file,
    delete_folder,
    write_file,
    read_file,
    list_directory,
    copy_file,
    move_file,
)

from colen.tools.app_tools import (
    open_application,
    open_file_with_app,
    find_window,
    focus_window,
    minimize_window,
    maximize_window,
    close_window,
    list_windows,
    move_window,
    resize_window,
)

from colen.tools.shell_tools import (
    execute_command,
    execute_powershell,
    get_environment_variable,
    set_environment_variable,
    list_processes,
    kill_process,
)

from colen.tools.content_tools import (
    generate_prompt,
    write_prompt_to_file,
    generate_code_snippet,
    generate_documentation,
)

__all__ = [
    # File tools
    "create_folder",
    "delete_file",
    "delete_folder",
    "write_file",
    "read_file",
    "list_directory",
    "copy_file",
    "move_file",
    # App tools
    "open_application",
    "open_file_with_app",
    "find_window",
    "focus_window",
    "minimize_window",
    "maximize_window",
    "close_window",
    "list_windows",
    "move_window",
    "resize_window",
    # Shell tools
    "execute_command",
    "execute_powershell",
    "get_environment_variable",
    "set_environment_variable",
    "list_processes",
    "kill_process",
    # Content tools
    "generate_prompt",
    "write_prompt_to_file",
    "generate_code_snippet",
    "generate_documentation",
]