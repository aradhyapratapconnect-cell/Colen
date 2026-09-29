"""Configuration management for Colen automation features.

This module provides centralized configuration for tool behavior, safety settings,
and user preferences.
"""

import os
from pathlib import Path
from typing import List, Set, Optional


class ColenConfig:
    """Centralized configuration for Colen automation features."""
    
    # Safety settings
    CONFIRMATION_MODE = os.environ.get("COLEN_CONFIRMATION_MODE", "smart")  # "strict", "smart", "relaxed"
    AUTO_CONFIRM_SAFE_OPERATIONS = CONFIRMATION_MODE != "strict"
    MAX_FILE_SIZE_MB = int(os.environ.get("COLEN_MAX_FILE_SIZE_MB", "100"))
    
    # Command execution settings
    MAX_COMMAND_TIMEOUT = int(os.environ.get("COLEN_MAX_COMMAND_TIMEOUT", "30"))
    
    # Path restrictions
    SAFE_DIRECTORIES = [
        Path.home(),
        Path.home() / "Documents",
        Path.home() / "Desktop",
        Path.home() / "Downloads",
        Path.cwd(),
    ]
    
    # Add user-specified safe directories from environment
    if safe_dirs := os.environ.get("COLEN_SAFE_DIRECTORIES"):
        for dir_path in safe_dirs.split(","):
            expanded = Path(dir_path.strip()).expanduser()
            if expanded.exists():
                SAFE_DIRECTORIES.append(expanded)
    
    PROTECTED_DIRECTORIES = [
        Path("C:/Windows"),
        Path("C:/Program Files"),
        Path("C:/Program Files (x86)"),
        Path("C:/ProgramData"),
    ]
    
    # Tool enablement
    ENABLE_TOOLS = os.environ.get("COLEN_ENABLE_TOOLS", "true").lower() == "true"
    ENABLE_FILE_OPERATIONS = True
    ENABLE_APP_OPERATIONS = True
    ENABLE_SHELL_COMMANDS = True
    ENABLE_WINDOW_MANAGEMENT = True
    ENABLE_CONTENT_GENERATION = True
    
    # High-risk operations that require confirmation (in smart mode)
    HIGH_RISK_OPERATIONS = {
        "delete_file",
        "delete_folder",
        "execute_command",
        "execute_powershell",
        "kill_process",
    }
    
    # Safe operations that can be auto-confirmed (in smart mode)
    SAFE_OPERATIONS = {
        "create_folder",
        "read_file",
        "list_directory",
        "list_windows",
        "list_processes",
        "get_environment_variable",
        "find_window",
    }
    
    # Audit logging
    AUDIT_LOG_PATH = Path(os.environ.get("COLEN_AUDIT_LOG_PATH", str(Path.home() / ".colen_audit.log")))
    
    @classmethod
    def is_confirmation_required(cls, operation: str) -> bool:
        """Check if an operation requires confirmation based on current mode.
        
        Args:
            operation: Name of the operation
            
        Returns:
            True if confirmation is required
        """
        if cls.CONFIRMATION_MODE == "strict":
            return True
        
        if cls.CONFIRMATION_MODE == "relaxed":
            return False
        
        # Smart mode
        return operation in cls.HIGH_RISK_OPERATIONS
    
    @classmethod
    def get_safe_directories(cls) -> List[Path]:
        """Get list of safe directories for operations.
        
        Returns:
            List of safe directory paths
        """
        return cls.SAFE_DIRECTORIES.copy()
    
    @classmethod
    def get_protected_directories(cls) -> List[Path]:
        """Get list of protected directories.
        
        Returns:
            List of protected directory paths
        """
        return cls.PROTECTED_DIRECTORIES.copy()
    
    @classmethod
    def add_safe_directory(cls, directory: Path) -> None:
        """Add a directory to the safe directories list.
        
        Args:
            directory: Directory path to add
        """
        expanded = directory.expanduser().resolve()
        if expanded not in cls.SAFE_DIRECTORIES:
            cls.SAFE_DIRECTORIES.append(expanded)
    
    @classmethod
    def is_tool_enabled(cls, tool_category: str) -> bool:
        """Check if a tool category is enabled.
        
        Args:
            tool_category: Category of tool ("file", "app", "shell", "window", "content")
            
        Returns:
            True if the tool category is enabled
        """
        if not cls.ENABLE_TOOLS:
            return False
        
        enabled_map = {
            "file": cls.ENABLE_FILE_OPERATIONS,
            "app": cls.ENABLE_APP_OPERATIONS,
            "shell": cls.ENABLE_SHELL_COMMANDS,
            "window": cls.ENABLE_WINDOW_MANAGEMENT,
            "content": cls.ENABLE_CONTENT_GENERATION,
        }
        
        return enabled_map.get(tool_category, True)


# Global config instance
_config_instance: Optional[ColenConfig] = None


def get_config() -> ColenConfig:
    """Get the global configuration instance.
    
    Returns:
        ColenConfig instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ColenConfig()
    return _config_instance