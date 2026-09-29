"""Tool schema definitions for Groq API function calling.

This module provides JSON schema definitions for all Colen tools that can be
passed to the Groq API for function calling capabilities.
"""

# File operation tool schemas
FILE_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "create_folder",
            "description": "Create a new folder at the specified path. Parent directories will be created if they don't exist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path where the folder should be created (e.g., 'C:/Users/Name/Documents/Project')"
                    },
                    "parents": {
                        "type": "boolean",
                        "description": "Create parent directories if they don't exist (default: true)",
                        "default": True
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file at the specified path. This operation requires user confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to delete"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_folder",
            "description": "Delete a folder at the specified path. This operation requires user confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the folder to delete"
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Delete folder and all its contents (default: false)",
                        "default": False
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file. Creates parent directories if needed and overwrites existing files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to write"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    },
                    "create_dirs": {
                        "type": "boolean",
                        "description": "Create parent directories if they don't exist (default: true)",
                        "default": True
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read content from a file. Returns the file contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to read"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List contents of a directory. Shows files and folders with their sizes and types.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the directory to list (default: current directory)",
                        "default": "."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "copy_file",
            "description": "Copy a file from source to destination. Creates parent directories if needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Path to the source file"
                    },
                    "destination": {
                        "type": "string",
                        "description": "Path to the destination"
                    }
                },
                "required": ["source", "destination"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "move_file",
            "description": "Move a file from source to destination. Creates parent directories if needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Path to the source file"
                    },
                    "destination": {
                        "type": "string",
                        "description": "Path to the destination"
                    }
                },
                "required": ["source", "destination"]
            }
        }
    }
]

# Application and window management tool schemas
APP_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": "Launch an application by name. Can include command-line arguments.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "Name of the application to launch (e.g., 'notepad', 'chrome', 'code')"
                    },
                    "args": {
                        "type": "string",
                        "description": "Optional command-line arguments for the application"
                    }
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_file_with_app",
            "description": "Open a file with a specific application or the default application for that file type.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to open"
                    },
                    "app_name": {
                        "type": "string",
                        "description": "Optional application name (uses default if not specified)"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_window",
            "description": "Find windows by title. Returns window information including position, size, and state.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Window title to search for (can be partial match)"
                    }
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "focus_window",
            "description": "Focus (bring to front) a window by title.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Window title to focus"
                    }
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "minimize_window",
            "description": "Minimize a window by title.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Window title to minimize"
                    }
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "maximize_window",
            "description": "Maximize a window by title.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Window title to maximize"
                    }
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "close_window",
            "description": "Close a window by title. This operation requires user confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Window title to close"
                    }
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_windows",
            "description": "List all visible windows with their titles, positions, and sizes.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "move_window",
            "description": "Move a window to specific screen coordinates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Window title to move"
                    },
                    "x": {
                        "type": "integer",
                        "description": "X coordinate for the window position"
                    },
                    "y": {
                        "type": "integer",
                        "description": "Y coordinate for the window position"
                    }
                },
                "required": ["title", "x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "resize_window",
            "description": "Resize a window to specific dimensions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Window title to resize"
                    },
                    "width": {
                        "type": "integer",
                        "description": "New width for the window"
                    },
                    "height": {
                        "type": "integer",
                        "description": "New height for the window"
                    }
                },
                "required": ["title", "width", "height"]
            }
        }
    }
]

# Shell command tool schemas
SHELL_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "Execute a shell command safely. Only whitelisted commands are allowed. This operation requires user confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Command to execute (e.g., 'dir', 'ping google.com', 'ipconfig')"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Maximum execution time in seconds (default: 30)",
                        "default": 30
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_powershell",
            "description": "Execute a PowerShell command. This operation requires user confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "PowerShell command to execute"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Maximum execution time in seconds (default: 30)",
                        "default": 30
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_environment_variable",
            "description": "Get the value of an environment variable.",
            "parameters": {
                "type": "object",
                "properties": {
                    "var_name": {
                        "type": "string",
                        "description": "Name of the environment variable (e.g., 'PATH', 'USERPROFILE')"
                    }
                },
                "required": ["var_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_environment_variable",
            "description": "Set the value of an environment variable for the current process.",
            "parameters": {
                "type": "object",
                "properties": {
                    "var_name": {
                        "type": "string",
                        "description": "Name of the environment variable"
                    },
                    "value": {
                        "type": "string",
                        "description": "Value to set for the environment variable"
                    }
                },
                "required": ["var_name", "value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_processes",
            "description": "List all running processes with their PID, name, CPU usage, and memory usage.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "kill_process",
            "description": "Kill a process by name. This operation requires user confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "process_name": {
                        "type": "string",
                        "description": "Name of the process to kill (e.g., 'notepad', 'chrome')"
                    }
                },
                "required": ["process_name"]
            }
        }
    }
]

# Content generation tool schemas
CONTENT_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "generate_prompt",
            "description": "Generate a prompt for a given topic and style. Useful for creating structured prompts for AI interactions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Topic for the prompt"
                    },
                    "style": {
                        "type": "string",
                        "description": "Style of the prompt (professional, casual, creative, technical)",
                        "enum": ["professional", "casual", "creative", "technical"],
                        "default": "professional"
                    }
                },
                "required": ["topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_prompt_to_file",
            "description": "Generate a prompt and write it to a file. Creates parent directories if needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Topic for the prompt"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Path to write the prompt to"
                    },
                    "style": {
                        "type": "string",
                        "description": "Style of the prompt (professional, casual, creative, technical)",
                        "enum": ["professional", "casual", "creative", "technical"],
                        "default": "professional"
                    }
                },
                "required": ["topic", "file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_code_snippet",
            "description": "Generate a code snippet for a given programming language and description.",
            "parameters": {
                "type": "object",
                "properties": {
                    "language": {
                        "type": "string",
                        "description": "Programming language (python, javascript, java, cpp)",
                        "enum": ["python", "javascript", "java", "cpp"]
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of what the code should do"
                    }
                },
                "required": ["language", "description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_documentation",
            "description": "Generate documentation for a given topic in various formats.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Topic to document"
                    },
                    "format": {
                        "type": "string",
                        "description": "Documentation format (markdown, html, plain)",
                        "enum": ["markdown", "html", "plain"],
                        "default": "markdown"
                    }
                },
                "required": ["topic"]
            }
        }
    }
]

# Combined all tool schemas
ALL_TOOL_SCHEMAS = FILE_TOOL_SCHEMAS + APP_TOOL_SCHEMAS + SHELL_TOOL_SCHEMAS + CONTENT_TOOL_SCHEMAS

# Tool function registry - maps schema names to actual function implementations
TOOL_REGISTRY = {
    # File tools
    "create_folder": "colen.tools.file_tools.create_folder",
    "delete_file": "colen.tools.file_tools.delete_file",
    "delete_folder": "colen.tools.file_tools.delete_folder",
    "write_file": "colen.tools.file_tools.write_file",
    "read_file": "colen.tools.file_tools.read_file",
    "list_directory": "colen.tools.file_tools.list_directory",
    "copy_file": "colen.tools.file_tools.copy_file",
    "move_file": "colen.tools.file_tools.move_file",
    # App tools
    "open_application": "colen.tools.app_tools.open_application",
    "open_file_with_app": "colen.tools.app_tools.open_file_with_app",
    "find_window": "colen.tools.app_tools.find_window",
    "focus_window": "colen.tools.app_tools.focus_window",
    "minimize_window": "colen.tools.app_tools.minimize_window",
    "maximize_window": "colen.tools.app_tools.maximize_window",
    "close_window": "colen.tools.app_tools.close_window",
    "list_windows": "colen.tools.app_tools.list_windows",
    "move_window": "colen.tools.app_tools.move_window",
    "resize_window": "colen.tools.app_tools.resize_window",
    # Shell tools
    "execute_command": "colen.tools.shell_tools.execute_command",
    "execute_powershell": "colen.tools.shell_tools.execute_powershell",
    "get_environment_variable": "colen.tools.shell_tools.get_environment_variable",
    "set_environment_variable": "colen.tools.shell_tools.set_environment_variable",
    "list_processes": "colen.tools.shell_tools.list_processes",
    "kill_process": "colen.tools.shell_tools.kill_process",
    # Content tools
    "generate_prompt": "colen.tools.content_tools.generate_prompt",
    "write_prompt_to_file": "colen.tools.content_tools.write_prompt_to_file",
    "generate_code_snippet": "colen.tools.content_tools.generate_code_snippet",
    "generate_documentation": "colen.tools.content_tools.generate_documentation",
}


def get_tool_schemas(categories: Optional[list] = None) -> list:
    """Get tool schemas for specified categories.
    
    Args:
        categories: List of categories to include ("file", "app", "shell", "content")
                   If None, returns all schemas.
        
    Returns:
        List of tool schema definitions
    """
    if categories is None:
        return ALL_TOOL_SCHEMAS
    
    schemas = []
    if "file" in categories:
        schemas.extend(FILE_TOOL_SCHEMAS)
    if "app" in categories:
        schemas.extend(APP_TOOL_SCHEMAS)
    if "shell" in categories:
        schemas.extend(SHELL_TOOL_SCHEMAS)
    if "content" in categories:
        schemas.extend(CONTENT_TOOL_SCHEMAS)
    
    return schemas


def get_tool_function(tool_name: str):
    """Get the actual function implementation for a tool name.
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        Function object or None if not found
    """
    import importlib
    
    module_path = TOOL_REGISTRY.get(tool_name)
    if not module_path:
        return None
    
    try:
        module_name, function_name = module_path.rsplit(".", 1)
        module = importlib.import_module(module_name)
        return getattr(module, function_name)
    except (ImportError, AttributeError):
        return None