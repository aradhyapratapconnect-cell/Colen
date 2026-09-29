"""Shell command execution tools for Colen.

This module provides safe shell command execution including running commands,
PowerShell scripts, environment variable management, and process control.
All operations include comprehensive security checks and audit logging.
"""

import subprocess
import time
from typing import Optional, List

from colen.tools.safety import (
    sanitize_command,
    is_command_allowed,
    require_confirmation,
    get_user_confirmation,
)
from colen.tools.audit import log_operation
from colen.config import get_config


def execute_command(command: str, timeout: int = 30) -> str:
    """Execute a shell command safely.
    
    Args:
        command: Command to execute
        timeout: Maximum execution time in seconds
        
    Returns:
        Command output (stdout and stderr)
    """
    config = get_config()
    params = {"command": command, "timeout": timeout}
    start_time = time.time()
    
    try:
        # Sanitize the command
        sanitized_parts = sanitize_command(command)
        
        # Check if command is allowed
        base_command = sanitized_parts[0] if sanitized_parts else ""
        if not is_command_allowed(base_command):
            return f"Command not allowed: {base_command}. Only whitelisted commands are permitted."
        
        # Always require confirmation for command execution
        if not get_user_confirmation(f"Execute command: '{command}'?"):
            return "Operation cancelled by user."
        
        # Use timeout from config if not specified
        actual_timeout = timeout if timeout > 0 else config.MAX_COMMAND_TIMEOUT
        
        # Execute the command safely (no shell=True)
        result = subprocess.run(
            sanitized_parts,
            capture_output=True,
            text=True,
            timeout=actual_timeout,
            shell=False,  # Critical for security
        )
        
        # Format output
        output = []
        if result.stdout:
            output.append(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            output.append(f"STDERR:\n{result.stderr}")
        output.append(f"EXIT CODE: {result.returncode}")
        
        result_str = "\n".join(output)
        execution_time = time.time() - start_time
        
        log_operation(
            "execute_command",
            params,
            f"Command completed with exit code {result.returncode}",
            success=result.returncode == 0,
            execution_time=execution_time,
            user_confirmed=True,
        )
        
        return result_str
        
    except subprocess.TimeoutExpired:
        error_msg = f"Command timed out after {actual_timeout} seconds"
        log_operation("execute_command", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg
    except ValueError as e:
        error_msg = f"Invalid command: {e}"
        log_operation("execute_command", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg
    except Exception as e:
        error_msg = f"Error executing command: {e}"
        log_operation("execute_command", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg


def execute_powershell(command: str, timeout: int = 30) -> str:
    """Execute a PowerShell command safely.
    
    Args:
        command: PowerShell command to execute
        timeout: Maximum execution time in seconds
        
    Returns:
        Command output
    """
    config = get_config()
    params = {"command": command, "timeout": timeout}
    start_time = time.time()
    
    try:
        # Always require confirmation for PowerShell execution
        if not get_user_confirmation(f"Execute PowerShell command: '{command}'?"):
            return "Operation cancelled by user."
        
        # Use timeout from config if not specified
        actual_timeout = timeout if timeout > 0 else config.MAX_COMMAND_TIMEOUT
        
        # Execute PowerShell command safely
        result = subprocess.run(
            ["powershell", "-Command", command],
            capture_output=True,
            text=True,
            timeout=actual_timeout,
        )
        
        # Format output
        output = []
        if result.stdout:
            output.append(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            output.append(f"STDERR:\n{result.stderr}")
        output.append(f"EXIT CODE: {result.returncode}")
        
        result_str = "\n".join(output)
        execution_time = time.time() - start_time
        
        log_operation(
            "execute_powershell",
            params,
            f"PowerShell command completed with exit code {result.returncode}",
            success=result.returncode == 0,
            execution_time=execution_time,
            user_confirmed=True,
        )
        
        return result_str
        
    except subprocess.TimeoutExpired:
        error_msg = f"PowerShell command timed out after {actual_timeout} seconds"
        log_operation("execute_powershell", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg
    except Exception as e:
        error_msg = f"Error executing PowerShell command: {e}"
        log_operation("execute_powershell", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg


def get_environment_variable(var_name: str) -> str:
    """Get the value of an environment variable.
    
    Args:
        var_name: Name of the environment variable
        
    Returns:
        Environment variable value or error message
    """
    import os
    params = {"var_name": var_name}
    start_time = time.time()
    
    try:
        value = os.environ.get(var_name)
        if value is None:
            result = f"Environment variable '{var_name}' not found"
        else:
            result = f"Environment variable '{var_name}': {value}"
        
        execution_time = time.time() - start_time
        
        log_operation(
            "get_environment_variable",
            params,
            result,
            success=True,
            execution_time=execution_time,
            user_confirmed=False,
        )
        
        return result
        
    except Exception as e:
        error_msg = f"Error getting environment variable: {e}"
        log_operation("get_environment_variable", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg


def set_environment_variable(var_name: str, value: str) -> str:
    """Set the value of an environment variable (current process only).
    
    Args:
        var_name: Name of the environment variable
        value: Value to set
        
    Returns:
        Success message
    """
    import os
    config = get_config()
    params = {"var_name": var_name, "value": value}
    start_time = time.time()
    
    try:
        # Check if confirmation is required
        if require_confirmation("set_environment_variable", params, config.CONFIRMATION_MODE):
            if not get_user_confirmation(f"Set environment variable '{var_name}' to '{value}'?"):
                return "Operation cancelled by user."
        
        os.environ[var_name] = value
        
        result = f"Successfully set environment variable '{var_name}' to '{value}'"
        execution_time = time.time() - start_time
        
        log_operation(
            "set_environment_variable",
            params,
            result,
            success=True,
            execution_time=execution_time,
            user_confirmed=require_confirmation("set_environment_variable", params, config.CONFIRMATION_MODE),
        )
        
        return result
        
    except Exception as e:
        error_msg = f"Error setting environment variable: {e}"
        log_operation("set_environment_variable", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg


def list_processes() -> str:
    """List all running processes.
    
    Returns:
        List of running processes with basic information
    """
    try:
        import psutil
        
        params = {}
        start_time = time.time()
        
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
            try:
                proc_info = f"PID: {proc.info['pid']:>6} | Name: {proc.info['name']:<20} | CPU: {proc.info['cpu_percent']:>5.1f}% | Memory: {proc.info['memory_percent']:>5.1f}%"
                processes.append(proc_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        if not processes:
            result = "No processes found"
        else:
            result = f"Running processes ({len(processes)} total):\n" + "\n".join(processes[:20])  # Limit to first 20
            if len(processes) > 20:
                result += f"\n... and {len(processes) - 20} more"
        
        execution_time = time.time() - start_time
        
        log_operation(
            "list_processes",
            params,
            f"Listed {len(processes)} processes",
            success=True,
            execution_time=execution_time,
            user_confirmed=False,
        )
        
        return result
        
    except ImportError:
        return "Error: psutil library not installed. Install with: pip install psutil"
    except Exception as e:
        error_msg = f"Error listing processes: {e}"
        log_operation("list_processes", {}, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg


def kill_process(process_name: str) -> str:
    """Kill a process by name.
    
    Args:
        process_name: Name of the process to kill
        
    Returns:
        Success message
    """
    config = get_config()
    params = {"process_name": process_name}
    start_time = time.time()
    
    try:
        import psutil
        
        # Always require confirmation for killing processes
        if not get_user_confirmation(f"Kill process '{process_name}'?"):
            return "Operation cancelled by user."
        
        killed = []
        not_found = []
        
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                    proc.kill()
                    killed.append(f"{proc.info['name']} (PID: {proc.pid})")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        if killed:
            result = f"Successfully killed processes: {', '.join(killed)}"
        else:
            result = f"No processes found matching '{process_name}'"
        
        execution_time = time.time() - start_time
        
        log_operation(
            "kill_process",
            params,
            result,
            success=len(killed) > 0,
            execution_time=execution_time,
            user_confirmed=True,
        )
        
        return result
        
    except ImportError:
        return "Error: psutil library not installed. Install with: pip install psutil"
    except Exception as e:
        error_msg = f"Error killing process: {e}"
        log_operation("kill_process", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg