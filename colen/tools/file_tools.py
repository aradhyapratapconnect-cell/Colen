"""File and folder operation tools for Colen.

This module provides safe file system operations including creating folders,
reading/writing files, deleting files/folders, and directory management.
All operations include comprehensive safety checks and audit logging.
"""

import os
import shutil
import time
from pathlib import Path
from typing import Optional

from colen.tools.safety import (
    validate_path,
    is_high_risk_operation,
    require_confirmation,
    get_user_confirmation,
    validate_file_size,
    sanitize_filename,
)
from colen.tools.audit import log_operation
from colen.config import get_config


def create_folder(path: str, parents: bool = True) -> str:
    """Create a new folder at the specified path.
    
    Args:
        path: Path where the folder should be created
        parents: Create parent directories if they don't exist
        
    Returns:
        Success message with folder path
    """
    config = get_config()
    params = {"path": path, "parents": parents}
    start_time = time.time()
    
    try:
        # Validate and sanitize the path
        validated_path = validate_path(path)
        
        # Check if confirmation is required
        if require_confirmation("create_folder", params, config.CONFIRMATION_MODE):
            if not get_user_confirmation(f"Create folder at '{validated_path}'?"):
                return "Operation cancelled by user."
        
        # Create the directory
        validated_path.mkdir(parents=parents, exist_ok=True)
        
        result = f"Successfully created folder: {validated_path}"
        execution_time = time.time() - start_time
        
        log_operation(
            "create_folder",
            params,
            result,
            success=True,
            execution_time=execution_time,
            user_confirmed=require_confirmation("create_folder", params, config.CONFIRMATION_MODE),
        )
        
        return result
        
    except (ValueError, PermissionError) as e:
        error_msg = f"Cannot create folder: {e}"
        log_operation("create_folder", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg
    except Exception as e:
        error_msg = f"Error creating folder: {e}"
        log_operation("create_folder", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg


def delete_file(path: str) -> str:
    """Delete a file at the specified path.
    
    Args:
        path: Path to the file to delete
        
    Returns:
        Success message with file path
    """
    config = get_config()
    params = {"path": path}
    start_time = time.time()
    
    try:
        # Validate and sanitize the path
        validated_path = validate_path(path)
        
        # Check if file exists
        if not validated_path.exists():
            return f"File does not exist: {validated_path}"
        
        if not validated_path.is_file():
            return f"Path is not a file: {validated_path}"
        
        # Always require confirmation for delete operations
        if not get_user_confirmation(f"Delete file '{validated_path}'?"):
            return "Operation cancelled by user."
        
        # Delete the file
        validated_path.unlink()
        
        result = f"Successfully deleted file: {validated_path}"
        execution_time = time.time() - start_time
        
        log_operation(
            "delete_file",
            params,
            result,
            success=True,
            execution_time=execution_time,
            user_confirmed=True,
        )
        
        return result
        
    except (ValueError, PermissionError) as e:
        error_msg = f"Cannot delete file: {e}"
        log_operation("delete_file", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg
    except Exception as e:
        error_msg = f"Error deleting file: {e}"
        log_operation("delete_file", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg


def delete_folder(path: str, recursive: bool = False) -> str:
    """Delete a folder at the specified path.
    
    Args:
        path: Path to the folder to delete
        recursive: Delete folder and all contents
        
    Returns:
        Success message with folder path
    """
    config = get_config()
    params = {"path": path, "recursive": recursive}
    start_time = time.time()
    
    try:
        # Validate and sanitize the path
        validated_path = validate_path(path)
        
        # Check if folder exists
        if not validated_path.exists():
            return f"Folder does not exist: {validated_path}"
        
        if not validated_path.is_dir():
            return f"Path is not a folder: {validated_path}"
        
        # Always require confirmation for delete operations
        confirm_msg = f"Delete folder '{validated_path}'"
        if recursive:
            confirm_msg += " and all its contents?"
        else:
            confirm_msg += "?"
        
        if not get_user_confirmation(confirm_msg):
            return "Operation cancelled by user."
        
        # Delete the folder
        if recursive:
            shutil.rmtree(validated_path)
        else:
            validated_path.rmdir()
        
        result = f"Successfully deleted folder: {validated_path}"
        execution_time = time.time() - start_time
        
        log_operation(
            "delete_folder",
            params,
            result,
            success=True,
            execution_time=execution_time,
            user_confirmed=True,
        )
        
        return result
        
    except (ValueError, PermissionError) as e:
        error_msg = f"Cannot delete folder: {e}"
        log_operation("delete_folder", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg
    except Exception as e:
        error_msg = f"Error deleting folder: {e}"
        log_operation("delete_folder", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg


def write_file(path: str, content: str, create_dirs: bool = True) -> str:
    """Write content to a file.
    
    Args:
        path: Path to the file to write
        content: Content to write to the file
        create_dirs: Create parent directories if they don't exist
        
    Returns:
        Success message with file path and size
    """
    config = get_config()
    params = {"path": path, "content_length": len(content), "create_dirs": create_dirs}
    start_time = time.time()
    
    try:
        # Validate and sanitize the path
        validated_path = validate_path(path)
        
        # Check file size
        content_size = len(content.encode('utf-8'))
        if not validate_file_size(content_size, config.MAX_FILE_SIZE_MB):
            return f"Content too large: {content_size} bytes (max: {config.MAX_FILE_SIZE_MB}MB)"
        
        # Check if confirmation is required
        if require_confirmation("write_file", params, config.CONFIRMATION_MODE):
            if validated_path.exists():
                if not get_user_confirmation(f"Overwrite existing file '{validated_path}'?"):
                    return "Operation cancelled by user."
            else:
                if not get_user_confirmation(f"Create file '{validated_path}' with content?"):
                    return "Operation cancelled by user."
        
        # Create parent directories if needed
        if create_dirs:
            validated_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the file
        validated_path.write_text(content, encoding='utf-8')
        
        result = f"Successfully wrote {content_size} bytes to: {validated_path}"
        execution_time = time.time() - start_time
        
        log_operation(
            "write_file",
            params,
            result,
            success=True,
            execution_time=execution_time,
            user_confirmed=require_confirmation("write_file", params, config.CONFIRMATION_MODE),
        )
        
        return result
        
    except (ValueError, PermissionError) as e:
        error_msg = f"Cannot write file: {e}"
        log_operation("write_file", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg
    except Exception as e:
        error_msg = f"Error writing file: {e}"
        log_operation("write_file", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg


def read_file(path: str) -> str:
    """Read content from a file.
    
    Args:
        path: Path to the file to read
        
    Returns:
        File content
    """
    config = get_config()
    params = {"path": path}
    start_time = time.time()
    
    try:
        # Validate and sanitize the path
        validated_path = validate_path(path)
        
        # Check if file exists
        if not validated_path.exists():
            return f"File does not exist: {validated_path}"
        
        if not validated_path.is_file():
            return f"Path is not a file: {validated_path}"
        
        # Read the file
        content = validated_path.read_text(encoding='utf-8')
        
        # Check file size
        content_size = len(content.encode('utf-8'))
        if not validate_file_size(content_size, config.MAX_FILE_SIZE_MB):
            return f"File too large to read: {content_size} bytes (max: {config.MAX_FILE_SIZE_MB}MB)"
        
        result = f"Successfully read {content_size} bytes from: {validated_path}\n\nContent:\n{content}"
        execution_time = time.time() - start_time
        
        log_operation(
            "read_file",
            params,
            f"Successfully read {content_size} bytes",
            success=True,
            execution_time=execution_time,
            user_confirmed=False,
        )
        
        return result
        
    except (ValueError, PermissionError) as e:
        error_msg = f"Cannot read file: {e}"
        log_operation("read_file", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg
    except Exception as e:
        error_msg = f"Error reading file: {e}"
        log_operation("read_file", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg


def list_directory(path: str = ".") -> str:
    """List contents of a directory.
    
    Args:
        path: Path to the directory to list (default: current directory)
        
    Returns:
        Directory listing
    """
    config = get_config()
    params = {"path": path}
    start_time = time.time()
    
    try:
        # Validate and sanitize the path
        validated_path = validate_path(path)
        
        # Check if directory exists
        if not validated_path.exists():
            return f"Directory does not exist: {validated_path}"
        
        if not validated_path.is_dir():
            return f"Path is not a directory: {validated_path}"
        
        # List directory contents
        items = []
        for item in validated_path.iterdir():
            item_type = "DIR " if item.is_dir() else "FILE"
            size = f"{item.stat().st_size} bytes" if item.is_file() else ""
            items.append(f"  {item_type:5} {size:15} {item.name}")
        
        if not items:
            result = f"Directory is empty: {validated_path}"
        else:
            result = f"Contents of {validated_path}:\n" + "\n".join(items)
        
        execution_time = time.time() - start_time
        
        log_operation(
            "list_directory",
            params,
            f"Listed {len(items)} items",
            success=True,
            execution_time=execution_time,
            user_confirmed=False,
        )
        
        return result
        
    except (ValueError, PermissionError) as e:
        error_msg = f"Cannot list directory: {e}"
        log_operation("list_directory", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg
    except Exception as e:
        error_msg = f"Error listing directory: {e}"
        log_operation("list_directory", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg


def copy_file(source: str, destination: str) -> str:
    """Copy a file from source to destination.
    
    Args:
        source: Path to the source file
        destination: Path to the destination
        
    Returns:
        Success message with paths
    """
    config = get_config()
    params = {"source": source, "destination": destination}
    start_time = time.time()
    
    try:
        # Validate and sanitize paths
        source_path = validate_path(source)
        dest_path = validate_path(destination)
        
        # Check if source exists
        if not source_path.exists():
            return f"Source file does not exist: {source_path}"
        
        if not source_path.is_file():
            return f"Source is not a file: {source_path}"
        
        # Check if confirmation is required
        if require_confirmation("copy_file", params, config.CONFIRMATION_MODE):
            if dest_path.exists():
                if not get_user_confirmation(f"Overwrite existing file '{dest_path}'?"):
                    return "Operation cancelled by user."
        
        # Create parent directories if needed
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy the file
        shutil.copy2(source_path, dest_path)
        
        result = f"Successfully copied '{source_path}' to '{dest_path}'"
        execution_time = time.time() - start_time
        
        log_operation(
            "copy_file",
            params,
            result,
            success=True,
            execution_time=execution_time,
            user_confirmed=require_confirmation("copy_file", params, config.CONFIRMATION_MODE),
        )
        
        return result
        
    except (ValueError, PermissionError) as e:
        error_msg = f"Cannot copy file: {e}"
        log_operation("copy_file", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg
    except Exception as e:
        error_msg = f"Error copying file: {e}"
        log_operation("copy_file", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg


def move_file(source: str, destination: str) -> str:
    """Move a file from source to destination.
    
    Args:
        source: Path to the source file
        destination: Path to the destination
        
    Returns:
        Success message with paths
    """
    config = get_config()
    params = {"source": source, "destination": destination}
    start_time = time.time()
    
    try:
        # Validate and sanitize paths
        source_path = validate_path(source)
        dest_path = validate_path(destination)
        
        # Check if source exists
        if not source_path.exists():
            return f"Source file does not exist: {source_path}"
        
        if not source_path.is_file():
            return f"Source is not a file: {source_path}"
        
        # Check if confirmation is required
        if require_confirmation("move_file", params, config.CONFIRMATION_MODE):
            if not get_user_confirmation(f"Move '{source_path}' to '{dest_path}'?"):
                return "Operation cancelled by user."
        
        # Create parent directories if needed
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Move the file
        shutil.move(str(source_path), str(dest_path))
        
        result = f"Successfully moved '{source_path}' to '{dest_path}'"
        execution_time = time.time() - start_time
        
        log_operation(
            "move_file",
            params,
            result,
            success=True,
            execution_time=execution_time,
            user_confirmed=require_confirmation("move_file", params, config.CONFIRMATION_MODE),
        )
        
        return result
        
    except (ValueError, PermissionError) as e:
        error_msg = f"Cannot move file: {e}"
        log_operation("move_file", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg
    except Exception as e:
        error_msg = f"Error moving file: {e}"
        log_operation("move_file", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg