"""Content generation tools for Colen.

This module provides tools for generating prompts, code snippets, documentation,
and other content. These tools use the LLM capabilities for content creation.
"""

import time
from typing import Optional

from colen.tools.safety import (
    validate_path,
    require_confirmation,
    get_user_confirmation,
)
from colen.tools.audit import log_operation
from colen.config import get_config


def generate_prompt(topic: str, style: str = "professional") -> str:
    """Generate a prompt for a given topic and style.
    
    Args:
        topic: Topic for the prompt
        style: Style of the prompt (professional, casual, creative, technical)
        
    Returns:
        Generated prompt text
    """
    config = get_config()
    params = {"topic": topic, "style": style}
    start_time = time.time()
    
    try:
        # Simple prompt generation based on style
        style_templates = {
            "professional": f"Please provide a professional response about {topic}. Include relevant details and maintain a formal tone.",
            "casual": f"Hey, can you tell me about {topic} in a casual, conversational way?",
            "creative": f"Let's get creative! Tell me something interesting and unique about {topic}.",
            "technical": f"Provide a technical explanation of {topic}. Include relevant technical details, specifications, and considerations.",
        }
        
        template = style_templates.get(style.lower(), style_templates["professional"])
        
        result = f"Generated prompt (style: {style}):\n{template}"
        execution_time = time.time() - start_time
        
        log_operation(
            "generate_prompt",
            params,
            result,
            success=True,
            execution_time=execution_time,
            user_confirmed=False,
        )
        
        return result
        
    except Exception as e:
        error_msg = f"Error generating prompt: {e}"
        log_operation("generate_prompt", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg


def write_prompt_to_file(topic: str, file_path: str, style: str = "professional") -> str:
    """Generate a prompt and write it to a file.
    
    Args:
        topic: Topic for the prompt
        file_path: Path to write the prompt to
        style: Style of the prompt
        
    Returns:
        Success message with file path
    """
    config = get_config()
    params = {"topic": topic, "file_path": file_path, "style": style}
    start_time = time.time()
    
    try:
        # Validate the file path
        validated_path = validate_path(file_path)
        
        # Generate the prompt
        prompt_result = generate_prompt(topic, style)
        
        # Extract just the prompt text (remove the "Generated prompt:" prefix)
        prompt_text = prompt_result.split(":\n", 1)[1] if ":\n" in prompt_result else prompt_result
        
        # Check if confirmation is required
        if require_confirmation("write_prompt_to_file", params, config.CONFIRMATION_MODE):
            if validated_path.exists():
                if not get_user_confirmation(f"Overwrite existing file '{validated_path}' with prompt?"):
                    return "Operation cancelled by user."
            else:
                if not get_user_confirmation(f"Create file '{validated_path}' with prompt?"):
                    return "Operation cancelled by user."
        
        # Create parent directories if needed
        validated_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the prompt to file
        validated_path.write_text(prompt_text, encoding='utf-8')
        
        result = f"Successfully wrote prompt to: {validated_path}"
        execution_time = time.time() - start_time
        
        log_operation(
            "write_prompt_to_file",
            params,
            result,
            success=True,
            execution_time=execution_time,
            user_confirmed=require_confirmation("write_prompt_to_file", params, config.CONFIRMATION_MODE),
        )
        
        return result
        
    except (ValueError, PermissionError) as e:
        error_msg = f"Cannot write prompt to file: {e}"
        log_operation("write_prompt_to_file", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg
    except Exception as e:
        error_msg = f"Error writing prompt to file: {e}"
        log_operation("write_prompt_to_file", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg


def generate_code_snippet(language: str, description: str) -> str:
    """Generate a code snippet for a given language and description.
    
    Args:
        language: Programming language (python, javascript, etc.)
        description: Description of what the code should do
        
    Returns:
        Generated code snippet
    """
    config = get_config()
    params = {"language": language, "description": description}
    start_time = time.time()
    
    try:
        # Simple code snippet templates
        code_templates = {
            "python": f"# Python code for: {description}\n# TODO: Implement the logic described above\nprint('{description}')",
            "javascript": f"// JavaScript code for: {description}\n// TODO: Implement the logic described above\nconsole.log('{description}');",
            "java": f"// Java code for: {description}\n// TODO: Implement the logic described above\npublic class Main {{\n    public static void main(String[] args) {{\n        System.out.println(\"{description}\");\n    }}\n}}",
            "cpp": f"// C++ code for: {description}\n// TODO: Implement the logic described above\n#include <iostream>\nint main() {{\n    std::cout << \"{description}\" << std::endl;\n    return 0;\n}}",
        }
        
        template = code_templates.get(language.lower(), code_templates["python"])
        
        result = f"Generated code snippet ({language}):\n{template}"
        execution_time = time.time() - start_time
        
        log_operation(
            "generate_code_snippet",
            params,
            result,
            success=True,
            execution_time=execution_time,
            user_confirmed=False,
        )
        
        return result
        
    except Exception as e:
        error_msg = f"Error generating code snippet: {e}"
        log_operation("generate_code_snippet", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg


def generate_documentation(topic: str, format: str = "markdown") -> str:
    """Generate documentation for a given topic.
    
    Args:
        topic: Topic to document
        format: Documentation format (markdown, html, plain)
        
    Returns:
        Generated documentation
    """
    config = get_config()
    params = {"topic": topic, "format": format}
    start_time = time.time()
    
    try:
        # Simple documentation templates
        doc_templates = {
            "markdown": f"# {topic}\n\n## Overview\nDocumentation for {topic}.\n\n## Details\nTODO: Add detailed documentation.\n\n## Usage\nTODO: Add usage examples.\n",
            "html": f"<!DOCTYPE html>\n<html>\n<head>\n    <title>{topic}</title>\n</head>\n<body>\n    <h1>{topic}</h1>\n    <p>Documentation for {topic}.</p>\n    <!-- TODO: Add detailed documentation -->\n</body>\n</html>",
            "plain": f"{topic}\n{'=' * len(topic)}\n\nDocumentation for {topic}.\n\nTODO: Add detailed documentation.",
        }
        
        template = doc_templates.get(format.lower(), doc_templates["markdown"])
        
        result = f"Generated documentation ({format}):\n{template}"
        execution_time = time.time() - start_time
        
        log_operation(
            "generate_documentation",
            params,
            result,
            success=True,
            execution_time=execution_time,
            user_confirmed=False,
        )
        
        return result
        
    except Exception as e:
        error_msg = f"Error generating documentation: {e}"
        log_operation("generate_documentation", params, error_msg, success=False, execution_time=time.time() - start_time)
        return error_msg