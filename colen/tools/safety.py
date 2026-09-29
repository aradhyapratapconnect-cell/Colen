"""Safety and security validations for Colen tools.

This module provides comprehensive security checks including path validation,
dangerous operation detection, smart confirmation logic, and command sanitization.
"""

import os
import re
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.prompt import Confirm

console = Console()

# High-risk operations that always require confirmation
HIGH_RISK_OPERATIONS = {
    "delete_file",
    "delete_folder",
    "execute_command",
    "execute_powershell",
    "kill_process",
    "format_drive",
    "shutdown",
}

# Safe operations that can be auto-confirmed
SAFE_OPERATIONS = {
    "create_folder",
    "read_file",
    "list_directory",
    "list_windows",
    "list_processes",
    "get_environment_variable",
    "find_window",
}

# Protected directories that should never be modified
PROTECTED_DIRECTORIES = {
    Path("C:/Windows"),
    Path("C:/Program Files"),
    Path("C:/Program Files (x86)"),
    Path("C:/ProgramData"),
    Path("C:/System32"),
}

# Safe directories where operations are generally allowed
SAFE_DIRECTORIES = {
    Path.home(),
    Path.home() / "Documents",
    Path.home() / "Desktop",
    Path.home() / "Downloads",
    Path.cwd(),
}

# Dangerous command patterns
DANGEROUS_COMMAND_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"del\s+/.*",
    r"format\s+[a-zA-Z]:",
    r"shutdown",
    r"reboot",
    r"halt",
    r":\s*>\s*/dev/",
    r"dd\s+if=.*of=",
]

# Allowed shell commands (whitelist)
ALLOWED_COMMANDS = {
    "dir",
    "ls",
    "cd",
    "pwd",
    "echo",
    "type",
    "cat",
    "ping",
    "ipconfig",
    "whoami",
    "date",
    "time",
    "hostname",
    "tasklist",
    "netstat",
}


def validate_path(path: str, base_dir: Optional[Path] = None) -> Path:
    """Validate and sanitize a file path to prevent directory traversal attacks.
    
    Args:
        path: User-provided path string
        base_dir: Base directory to constrain operations to (optional)
        
    Returns:
        Validated Path object
        
    Raises:
        ValueError: If path is invalid or attempts traversal
        PermissionError: If path is in a protected directory
    """
    try:
        # Convert to Path object and resolve to absolute path
        user_path = Path(path).expanduser().resolve()
        
        # Check for path traversal attempts
        if ".." in str(path) or "~" in str(path):
            # Only allow if it resolves to a safe location
            if not any(str(user_path).startswith(str(safe_dir)) for safe_dir in SAFE_DIRECTORIES):
                raise ValueError(f"Path traversal detected: {path}")
        
        # Check if path is in protected directory
        for protected_dir in PROTECTED_DIRECTORIES:
            try:
                if str(user_path).startswith(str(protected_dir.resolve())):
                    raise PermissionError(f"Cannot access protected directory: {protected_dir}")
            except (OSError, RuntimeError):
                continue
        
        # If base_dir is specified, ensure path is within it
        if base_dir:
            base = base_dir.resolve()
            try:
                user_path.relative_to(base)
            except ValueError:
                raise ValueError(f"Path must be within {base_dir}: {path}")
        
        return user_path
        
    except (OSError, RuntimeError) as e:
        raise ValueError(f"Invalid path: {path}") from e


def is_dangerous_operation(operation: str, params: dict) -> bool:
    """Check if an operation is potentially dangerous.
    
    Args:
        operation: Name of the operation/tool
        params: Parameters passed to the operation
        
    Returns:
        True if operation is dangerous
    """
    # Check against high-risk operations list
    if operation in HIGH_RISK_OPERATIONS:
        return True
    
    # Check for dangerous parameters
    if "path" in params:
        path = str(params["path"])
        dangerous_keywords = ["windows", "system32", "program files", "boot"]
        if any(keyword in path.lower() for keyword in dangerous_keywords):
            return True
    
    if "command" in params:
        command = str(params["command"]).lower()
        for pattern in DANGEROUS_COMMAND_PATTERNS:
            if re.search(pattern, command):
                return True
    
    return False


def is_high_risk_operation(operation: str, params: dict) -> bool:
    """Check if an operation requires confirmation (smart confirmation logic).
    
    This is more nuanced than is_dangerous_operation - it checks if the specific
    invocation is high-risk, not just if the operation type can be dangerous.
    
    Args:
        operation: Name of the operation/tool
        params: Parameters passed to the operation
        
    Returns:
        True if operation requires user confirmation
    """
    # Safe operations never require confirmation
    if operation in SAFE_OPERATIONS:
        return False
    
    # High-risk operations always require confirmation
    if operation in HIGH_RISK_OPERATIONS:
        return True
    
    # Context-specific checks
    if operation == "write_file":
        # Writing to safe locations is low-risk
        if "path" in params:
            try:
                path = validate_path(params["path"])
                if any(str(path).startswith(str(safe_dir)) for safe_dir in SAFE_DIRECTORIES):
                    return False
            except (ValueError, PermissionError):
                return True
        return True
    
    if operation == "create_folder":
        # Creating folders in safe locations is low-risk
        if "path" in params:
            try:
                path = validate_path(params["path"])
                if any(str(path).startswith(str(safe_dir)) for safe_dir in SAFE_DIRECTORIES):
                    return False
            except (ValueError, PermissionError):
                return True
        return True
    
    # Default to requiring confirmation for unknown operations
    return True


def require_confirmation(operation: str, params: dict, config_mode: str = "smart") -> bool:
    """Determine if an operation requires user confirmation based on config mode.
    
    Args:
        operation: Name of the operation/tool
        params: Parameters passed to the operation
        config_mode: Configuration mode ("strict", "smart", "relaxed")
        
    Returns:
        True if confirmation is required
    """
    if config_mode == "strict":
        return True  # Always confirm in strict mode
    
    if config_mode == "relaxed":
        return False  # Never confirm in relaxed mode
    
    # Smart mode (default)
    return is_high_risk_operation(operation, params)


def get_user_confirmation(message: str) -> bool:
    """Get user confirmation for a dangerous operation.
    
    Args:
        message: Confirmation message to display
        
    Returns:
        True if user confirms, False otherwise
    """
    try:
        return Confirm.ask(f"[yellow]⚠ {message}[/yellow]", console=console)
    except (EOFError, KeyboardInterrupt):
        return False


def sanitize_command(command: str) -> List[str]:
    """Sanitize a shell command to prevent injection attacks.
    
    Args:
        command: User-provided command string
        
    Returns:
        List of sanitized command arguments
        
    Raises:
        ValueError: If command contains dangerous patterns
    """
    command_lower = command.lower()
    
    # Check for dangerous patterns
    for pattern in DANGEROUS_COMMAND_PATTERNS:
        if re.search(pattern, command_lower):
            raise ValueError(f"Dangerous command pattern detected: {pattern}")
    
    # Simple sanitization - split by spaces and quotes
    # This is basic; production systems should use proper parsing
    parts = []
    current = ""
    in_quotes = False
    
    for char in command:
        if char in ('"', "'"):
            in_quotes = not in_quotes
        elif char.isspace() and not in_quotes:
            if current:
                parts.append(current)
                current = ""
        else:
            current += char
    
    if current:
        parts.append(current)
    
    return parts if parts else [command]


def is_command_allowed(command: str) -> bool:
    """Check if a command is in the allowed whitelist.
    
    Args:
        command: Command to check
        
    Returns:
        True if command is allowed
    """
    # Extract the base command (first word)
    parts = command.split()
    if not parts:
        return False
    
    base_command = parts[0].lower()
    return base_command in ALLOWED_COMMANDS


def validate_file_size(size_bytes: int, max_size_mb: int = 100) -> bool:
    """Validate that a file size is within acceptable limits.
    
    Args:
        size_bytes: File size in bytes
        max_size_mb: Maximum allowed size in megabytes
        
    Returns:
        True if size is acceptable
    """
    max_bytes = max_size_mb * 1024 * 1024
    return size_bytes <= max_bytes


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to remove dangerous characters.
    
    Args:
        filename: User-provided filename
        
    Returns:
        Sanitized filename
    """
    # Remove dangerous characters
    dangerous_chars = '<>:"/\\|?*'
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename or "unnamed"