"""Tool calling orchestration engine for Colen.

This module provides the agent that orchestrates tool calling with the Groq API,
handling the conversation loop, tool execution, and response generation.
"""

import json
import time
from typing import List, Dict, Any, Optional, Iterator
import requests

from colen.tools.schemas import get_tool_schemas, get_tool_function
from colen.config import get_config


class ToolCallingAgent:
    """Agent that orchestrates tool calling with Groq API."""
    
    def __init__(self, model: str = "llama-3.1-8b-instant"):
        """Initialize the tool calling agent.
        
        Args:
            model: Groq model to use for tool calling
        """
        self.model = model
        self.config = get_config()
        self.conversation_history: List[Dict[str, Any]] = []
        self.tool_schemas = get_tool_schemas() if self.config.ENABLE_TOOLS else []
        
        # Groq API configuration
        self.groq_url = "https://api.groq.com/openai/v1/chat/completions"
        self.api_key = self._get_api_key()
        
        # Fallback models for when the primary model is not available
        self.fallback_models = ["openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
    
    def _get_api_key(self) -> str:
        """Get the Groq API key from environment."""
        import os
        api_key = os.environ.get("GROQ_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Set it in .env file or environment."
            )
        return api_key
    
    def _make_api_request(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Make a request to the Groq API with model fallback support.
        
        Args:
            messages: Conversation messages
            tools: Tool definitions to include
            
        Returns:
            API response
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        # Try the primary model first, then fallback models
        models_to_try = [self.model] + [m for m in self.fallback_models if m != self.model]
        
        for model in models_to_try:
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "temperature": 0.6,
                "max_tokens": 1000,
            }
            
            if tools:
                payload["tools"] = tools
            
            try:
                response = requests.post(
                    self.groq_url,
                    headers=headers,
                    json=payload,
                    timeout=(5, 60),
                )
                
                if response.status_code == 200:
                    # Update the model if we had to fall back
                    if model != self.model:
                        self.model = model
                    return response.json()
                elif response.status_code == 404:
                    # Model not found, try next fallback
                    continue
                else:
                    # Other error, raise immediately
                    raise RuntimeError(f"Groq API request failed (HTTP {response.status_code}): {response.text}")
                    
            except requests.RequestException as e:
                if model == models_to_try[-1]:  # Last model to try
                    raise RuntimeError(f"Groq API request failed: {str(e)}")
                continue
        
        raise RuntimeError(f"None of the models {models_to_try} are accessible on this Groq key.")
    
    def _execute_tool_call(self, tool_call: Dict[str, Any]) -> str:
        """Execute a tool call and return the result.
        
        Args:
            tool_call: Tool call from the API response
            
        Returns:
            Tool execution result
        """
        function_name = tool_call["function"]["name"]
        function_args = json.loads(tool_call["function"]["arguments"])
        
        # Get the actual function
        tool_function = get_tool_function(function_name)
        if not tool_function:
            return f"Error: Tool function '{function_name}' not found"
        
        try:
            # Execute the function with the provided arguments
            result = tool_function(**function_args)
            return result
        except Exception as e:
            return f"Error executing tool '{function_name}': {str(e)}"
    
    def process_message(self, user_message: str, history: Optional[List[Dict[str, Any]]] = None) -> Iterator[str]:
        """Process a user message with tool calling support.
        
        Args:
            user_message: User's message
            history: Optional conversation history
            
        Yields:
            Response tokens/strings as they are generated
        """
        # Build conversation context
        messages = []
        
        # System prompt
        system_prompt = (
            "You are Colen, a concise Jarvis-style assistant with system automation capabilities. "
            "Answer directly and correctly in at most 2-3 short sentences. "
            "Use tools when the user requests file operations, application launching, "
            "shell commands, window management, or content generation. "
            "Plain text only - no markdown, no lists, no emojis."
        )
        messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history if provided
        if history:
            messages.extend(history)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Tool calling loop
        max_iterations = 5  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            try:
                # Make API request with tools
                response = self._make_api_request(messages, self.tool_schemas)
                
                # Check if there are tool calls
                message = response["choices"][0]["message"]
                
                if "tool_calls" in message and message["tool_calls"]:
                    # Execute tool calls
                    tool_messages = []
                    
                    for tool_call in message["tool_calls"]:
                        # Execute the tool
                        result = self._execute_tool_call(tool_call)
                        
                        # Add tool result to messages
                        tool_messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": result
                        })
                    
                    # Add assistant message with tool calls
                    messages.append(message)
                    # Add tool results
                    messages.extend(tool_messages)
                    
                    # Continue the loop to get the final response
                    continue
                else:
                    # No tool calls, return the final response
                    final_response = message.get("content", "")
                    
                    # Update conversation history
                    self.conversation_history.append({"role": "user", "content": user_message})
                    self.conversation_history.append({"role": "assistant", "content": final_response})
                    
                    # Keep history manageable
                    if len(self.conversation_history) > 20:
                        self.conversation_history = self.conversation_history[-20:]
                    
                    yield final_response
                    return
                    
            except Exception as e:
                error_msg = f"Error in tool calling: {str(e)}"
                yield error_msg
                return
        
        # If we exit the loop without returning, something went wrong
        yield "I encountered an issue processing your request. Please try again."
    
    def process_message_streaming(self, user_message: str, history: Optional[List[Dict[str, Any]]] = None) -> Iterator[str]:
        """Process a user message with streaming response (future enhancement).
        
        Args:
            user_message: User's message
            history: Optional conversation history
            
        Yields:
            Response tokens as they are generated
        """
        # For now, use the non-streaming version
        # TODO: Implement streaming with tool calling
        for response in self.process_message(user_message, history):
            yield response
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the current conversation history.
        
        Returns:
            Conversation history
        """
        return self.conversation_history.copy()
    
    def clear_conversation_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history.clear()
    
    def update_tools(self, categories: Optional[List[str]] = None) -> None:
        """Update the available tools.
        
        Args:
            categories: Tool categories to enable (None = all enabled categories)
        """
        if self.config.ENABLE_TOOLS:
            self.tool_schemas = get_tool_schemas(categories)
        else:
            self.tool_schemas = []


def create_agent(model: str = "llama-3.1-8b-instant") -> ToolCallingAgent:
    """Create a tool calling agent instance.
    
    Args:
        model: Groq model to use
        
    Returns:
        ToolCallingAgent instance
    """
    return ToolCallingAgent(model=model)