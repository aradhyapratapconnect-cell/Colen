"""Application and window management tools for Colen.

This module provides tools for launching applications, opening files with specific
apps, and managing windows (focus, minimize, maximize, move, resize, etc.).
All operations include comprehensive safety checks and audit logging.
"""

import os
import subprocess
import time
from pathlib import Path
from typing import Optional

from colen.tools.safety import (
    validate_path,
    require_confirmation,
    get_user_confirmation,
)
from colen.tools.audit import log_operation
from colen.config import get_config


def open_application(app_name: str, args: Optional[str] = None) -> str:
    """Launch an application by name.
    
    Args:
        app_name: Name of the application to launch
        args: Optional command-line arguments
        
    Returns:
        Success message with application status
    """
    config = get_config()
    params = {"app_name": app_name, "args": args}
    start_time = time.time()
    
    try:
        # Check if confirmation is required
        if require_confirmation("open_application", params, config.CONFIRMATION_MODE):
            if not get_user_confirmation(f"Launch application '{app_name}'?"):
                return "Operation cancelled by user."
        
        # Try to find and launch the application
        # On Windows, use start command or direct path
        if os.name == 'nt':
            # Try using Windows start command
            command = ["start", "", app_name]
            if args:
                command.extend(args.split())
            
            # Use shell=True for start command (it's a Windows built-in)
            subprocess.Popen(command, shell=True)
        else:
            # On Unix-like systems, try common locations
            command = [app_name]
            if args:
                command.extend(args.split())
            
            subprocess.Popen(command, shell=False)
        
        result = f"Successfully launched application: {app_name}"
        execution_time = time.time() - start_time
        
        log_operation(
            "open_application",
            params,
            result,
            success=True,
            execution_time=execution_time,
            user_confirmed=require_confirmation("open_application", params, config.CONFIRMATION_MODE),
        )
        
        return result
        
    except Exception as e:
        error_msg = f"Error launching application: {e}"
        log_operation("open_application", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg


def open_file_with_app(file_path: str, app_name: Optional[str] = None) -> str:
    """Open a file with a specific application.
    
    Args:
        file_path: Path to the file to open
        app_name: Optional application name (uses default if not specified)
        
    Returns:
        Success message
    """
    config = get_config()
    params = {"file_path": file_path, "app_name": app_name}
    start_time = time.time()
    
    try:
        # Validate the file path
        validated_path = validate_path(file_path)
        
        # Check if file exists
        if not validated_path.exists():
            return f"File does not exist: {validated_path}"
        
        # Check if confirmation is required
        if require_confirmation("open_file_with_app", params, config.CONFIRMATION_MODE):
            if not get_user_confirmation(f"Open file '{validated_path}'?"):
                return "Operation cancelled by user."
        
        # Open the file
        if os.name == 'nt':
            if app_name:
                # Open with specific app
                subprocess.Popen([app_name, str(validated_path)], shell=False)
            else:
                # Use default application
                os.startfile(str(validated_path))
        else:
            if app_name:
                subprocess.Popen([app_name, str(validated_path)], shell=False)
            else:
                # Use xdg-open on Linux, open on macOS
                if os.name == 'darwin':
                    subprocess.Popen(["open", str(validated_path)], shell=False)
                else:
                    subprocess.Popen(["xdg-open", str(validated_path)], shell=False)
        
        result = f"Successfully opened file: {validated_path}"
        execution_time = time.time() - start_time
        
        log_operation(
            "open_file_with_app",
            params,
            result,
            success=True,
            execution_time=execution_time,
            user_confirmed=require_confirmation("open_file_with_app", params, config.CONFIRMATION_MODE),
        )
        
        return result
        
    except (ValueError, PermissionError) as e:
        error_msg = f"Cannot open file: {e}"
        log_operation("open_file_with_app", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg
    except Exception as e:
        error_msg = f"Error opening file: {e}"
        log_operation("open_file_with_app", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg


def find_window(title: str) -> str:
    """Find a window by title.
    
    Args:
        title: Window title to search for
        
    Returns:
        Window information or error message
    """
    try:
        import pywinctl as pwc
        
        params = {"title": title}
        start_time = time.time()
        
        # Search for windows matching the title
        windows = pwc.getWindowsWithTitle(title)
        
        if not windows:
            result = f"No windows found matching '{title}'"
        else:
            window_info = []
            for window in windows:
                window_info.append(f"  Title: {window.title}")
                window_info.append(f"  Position: {window.left}, {window.top}")
                window_info.append(f"  Size: {window.width}x{window.height}")
                window_info.append(f"  Visible: {window.isVisible}")
                window_info.append(f"  Minimized: {window.isMinimized}")
                window_info.append(f"  Maximized: {window.isMaximized}")
                window_info.append("")
            
            result = f"Found {len(windows)} window(s) matching '{title}':\n" + "\n".join(window_info)
        
        execution_time = time.time() - start_time
        
        log_operation(
            "find_window",
            params,
            f"Found {len(windows)} windows",
            success=True,
            execution_time=execution_time,
            user_confirmed=False,
        )
        
        return result
        
    except ImportError:
        return "Error: pywinctl library not installed. Install with: pip install pywinctl"
    except Exception as e:
        error_msg = f"Error finding window: {e}"
        log_operation("find_window", {"title": title}, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg


def focus_window(title: str) -> str:
    """Focus (bring to front) a window by title.
    
    Args:
        title: Window title to focus
        
    Returns:
        Success message
    """
    config = get_config()
    params = {"title": title}
    start_time = time.time()
    
    try:
        import pywinctl as pwc
        
        # Find windows matching the title
        windows = pwc.getWindowsWithTitle(title)
        
        if not windows:
            result = f"No windows found matching '{title}'"
        else:
            # Focus the first matching window
            window = windows[0]
            window.activate()
            result = f"Successfully focused window: {window.title}"
        
        execution_time = time.time() - start_time
        
        log_operation(
            "focus_window",
            params,
            result,
            success=len(windows) > 0,
            execution_time=execution_time,
            user_confirmed=False,
        )
        
        return result
        
    except ImportError:
        return "Error: pywinctl library not installed. Install with: pip install pywinctl"
    except Exception as e:
        error_msg = f"Error focusing window: {e}"
        log_operation("focus_window", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg


def minimize_window(title: str) -> str:
    """Minimize a window by title.
    
    Args:
        title: Window title to minimize
        
    Returns:
        Success message
    """
    config = get_config()
    params = {"title": title}
    start_time = time.time()
    
    try:
        import pywinctl as pwc
        
        # Find windows matching the title
        windows = pwc.getWindowsWithTitle(title)
        
        if not windows:
            result = f"No windows found matching '{title}'"
        else:
            # Minimize the first matching window
            window = windows[0]
            window.minimize()
            result = f"Successfully minimized window: {window.title}"
        
        execution_time = time.time() - start_time
        
        log_operation(
            "minimize_window",
            params,
            result,
            success=len(windows) > 0,
            execution_time=execution_time,
            user_confirmed=False,
        )
        
        return result
        
    except ImportError:
        return "Error: pywinctl library not installed. Install with: pip install pywinctl"
    except Exception as e:
        error_msg = f"Error minimizing window: {e}"
        log_operation("minimize_window", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg


def maximize_window(title: str) -> str:
    """Maximize a window by title.
    
    Args:
        title: Window title to maximize
        
    Returns:
        Success message
    """
    config = get_config()
    params = {"title": title}
    start_time = time.time()
    
    try:
        import pywinctl as pwc
        
        # Find windows matching the title
        windows = pwc.getWindowsWithTitle(title)
        
        if not windows:
            result = f"No windows found matching '{title}'"
        else:
            # Maximize the first matching window
            window = windows[0]
            window.maximize()
            result = f"Successfully maximized window: {window.title}"
        
        execution_time = time.time() - start_time
        
        log_operation(
            "maximize_window",
            params,
            result,
            success=len(windows) > 0,
            execution_time=execution_time,
            user_confirmed=False,
        )
        
        return result
        
    except ImportError:
        return "Error: pywinctl library not installed. Install with: pip install pywinctl"
    except Exception as e:
        error_msg = f"Error maximizing window: {e}"
        log_operation("maximize_window", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg


def close_window(title: str) -> str:
    """Close a window by title.
    
    Args:
        title: Window title to close
        
    Returns:
        Success message
    """
    config = get_config()
    params = {"title": title}
    start_time = time.time()
    
    try:
        import pywinctl as pwc
        
        # Always require confirmation for closing windows
        if not get_user_confirmation(f"Close window '{title}'?"):
            return "Operation cancelled by user."
        
        # Find windows matching the title
        windows = pwc.getWindowsWithTitle(title)
        
        if not windows:
            result = f"No windows found matching '{title}'"
        else:
            # Close the first matching window
            window = windows[0]
            window.close()
            result = f"Successfully closed window: {window.title}"
        
        execution_time = time.time() - start_time
        
        log_operation(
            "close_window",
            params,
            result,
            success=len(windows) > 0,
            execution_time=execution_time,
            user_confirmed=True,
        )
        
        return result
        
    except ImportError:
        return "Error: pywinctl library not installed. Install with: pip install pywinctl"
    except Exception as e:
        error_msg = f"Error closing window: {e}"
        log_operation("close_window", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg


def list_windows() -> str:
    """List all visible windows.
    
    Returns:
        List of all visible windows
    """
    try:
        import pywinctl as pwc
        
        params = {}
        start_time = time.time()
        
        # Get all windows
        windows = pwc.getAllWindows()
        
        if not windows:
            result = "No visible windows found"
        else:
            window_info = []
            for window in windows:
                window_info.append(f"  Title: {window.title}")
                window_info.append(f"  Position: ({window.left}, {window.top})")
                window_info.append(f"  Size: {window.width}x{window.height}")
                window_info.append("")
            
            result = f"Found {len(windows)} visible window(s):\n" + "\n".join(window_info[:30])  # Limit to first 30
            if len(windows) > 30:
                result += f"\n... and {len(windows) - 30} more"
        
        execution_time = time.time() - start_time
        
        log_operation(
            "list_windows",
            params,
            f"Listed {len(windows)} windows",
            success=True,
            execution_time=execution_time,
            user_confirmed=False,
        )
        
        return result
        
    except ImportError:
        return "Error: pywinctl library not installed. Install with: pip install pywinctl"
    except Exception as e:
        error_msg = f"Error listing windows: {e}"
        log_operation("list_windows", {}, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg


def move_window(title: str, x: int, y: int) -> str:
    """Move a window to specific coordinates.
    
    Args:
        title: Window title to move
        x: X coordinate
        y: Y coordinate
        
    Returns:
        Success message
    """
    config = get_config()
    params = {"title": title, "x": x, "y": y}
    start_time = time.time()
    
    try:
        import pywinctl as pwc
        
        # Find windows matching the title
        windows = pwc.getWindowsWithTitle(title)
        
        if not windows:
            result = f"No windows found matching '{title}'"
        else:
            # Move the first matching window
            window = windows[0]
            window.moveTo(x, y)
            result = f"Successfully moved window '{window.title}' to ({x}, {y})"
        
        execution_time = time.time() - start_time
        
        log_operation(
            "move_window",
            params,
            result,
            success=len(windows) > 0,
            execution_time=execution_time,
            user_confirmed=False,
        )
        
        return result
        
    except ImportError:
        return "Error: pywinctl library not installed. Install with: pip install pywinctl"
    except Exception as e:
        error_msg = f"Error moving window: {e}"
        log_operation("move_window", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg


def resize_window(title: str, width: int, height: int) -> str:
    """Resize a window to specific dimensions.
    
    Args:
        title: Window title to resize
        width: New width
        height: New height
        
    Returns:
        Success message
    """
    config = get_config()
    params = {"title": title, "width": width, "height": height}
    start_time = time.time()
    
    try:
        import pywinctl as pwc
        
        # Find windows matching the title
        windows = pwc.getWindowsWithTitle(title)
        
        if not windows:
            result = f"No windows found matching '{title}'"
        else:
            # Resize the first matching window
            window = windows[0]
            window.resizeTo(width, height)
            result = f"Successfully resized window '{window.title}' to {width}x{height}"
        
        execution_time = time.time() - start_time
        
        log_operation(
            "resize_window",
            params,
            result,
            success=len(windows) > 0,
            execution_time=execution_time,
            user_confirmed=False,
        )
        
        return result
        
    except ImportError:
        return "Error: pywinctl library not installed. Install with: pip install pywinctl"
    except Exception as e:
        error_msg = f"Error resizing window: {e}"
        log_operation("resize_window", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg