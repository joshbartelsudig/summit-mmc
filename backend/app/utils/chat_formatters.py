"""
Utility functions for formatting chat messages for different models.
"""

from typing import List, Dict, Any, Optional
from app.models.schemas import Message
from app.utils.constants import (
    DEFAULT_MARKDOWN_SYSTEM_PROMPT,
    MODEL_GPT,
    MODEL_CLAUDE,
    MODEL_TITAN,
    MODEL_COHERE,
    MODEL_LLAMA
)


def format_code_blocks(content: str) -> str:
    """
    Format code blocks with proper newlines.
    
    Args:
        content (str): The content to format
        
    Returns:
        str: Formatted content
    """
    if "```" not in content:
        return content
        
    # If this is an opening code block marker
    if content.strip().startswith("```") and not content.strip().endswith("```"):
        # Ensure there's a newline after the language identifier
        if not content.endswith('\n'):
            content += '\n'
    # If this is a closing code block marker
    elif content.strip() == "```" or content.strip().endswith("```"):
        # Ensure there's a newline before the closing marker
        if not content.startswith('\n'):
            content = '\n' + content
        # Ensure there's a newline after the closing marker
        if not content.endswith('\n'):
            content += '\n'
            
    return content


def prepare_messages_with_system_prompt(
    messages: List[Message], 
    system_prompt: Optional[str] = None,
    model: str = ""
) -> tuple[List[Message], Optional[str]]:
    """
    Prepare messages with system prompt based on model type.
    
    Args:
        messages (List[Message]): List of messages
        system_prompt (Optional[str]): Custom system prompt
        model (str): Model identifier
        
    Returns:
        tuple[List[Message], Optional[str]]: Tuple of (processed messages, system content)
    """
    messages = list(messages)
    system_content = None
    
    # Use custom system prompt if provided, otherwise use default
    system_prompt = system_prompt if system_prompt else DEFAULT_MARKDOWN_SYSTEM_PROMPT
    
    if model.startswith(MODEL_CLAUDE):
        # For Anthropic models, system message needs to be handled differently
        system_content = system_prompt
        non_system_messages = []
        for msg in messages:
            if msg.role == "system":
                system_content += "\n\n" + msg.content
            else:
                non_system_messages.append(msg)
        messages = non_system_messages
    else:
        # For other models like GPT, add system message if not present
        if not any(msg.role == "system" for msg in messages):
            messages.insert(0, Message(role="system", content=system_prompt))
    
    return messages, system_content


def format_messages_for_claude(
    messages: List[Message], 
    system_prompt: str
) -> tuple[List[Dict[str, Any]], str]:
    """
    Format messages for Claude API.
    
    Args:
        messages (List[Message]): List of messages
        system_prompt (str): System prompt
        
    Returns:
        tuple[List[Dict[str, Any]], str]: Tuple of (formatted messages, system message)
    """
    formatted_messages = []
    system_message = system_prompt
    
    for msg in messages:
        if msg.role == "system":
            system_message = msg.content + "\n\n" + system_prompt
        else:
            formatted_messages.append({
                "role": msg.role,
                "content": [{"type": "text", "text": msg.content}]
            })
    
    return formatted_messages, system_message


def format_messages_for_titan(messages: List[Message]) -> str:
    """
    Format messages for Titan model.
    
    Args:
        messages (List[Message]): List of messages
        
    Returns:
        str: Formatted input text
    """
    formatted_messages = []
    system_messages = []
    
    # First, extract system messages
    for msg in messages:
        if msg.role == "system":
            system_messages.append(f"System: {msg.content}")
    
    # Add all system messages at the beginning
    if system_messages:
        formatted_messages.extend(system_messages)
        # Add an empty line after system messages for better separation
        formatted_messages.append("")
    
    # Then add user and assistant messages
    for msg in messages:
        if msg.role == "user":
            formatted_messages.append(f"Human: {msg.content}")
        elif msg.role == "assistant":
            formatted_messages.append(f"Assistant: {msg.content}")
    
    formatted_messages.append("Assistant: ")
    return "\n".join(formatted_messages)


def format_messages_for_cohere(messages: List[Message]) -> List[Dict[str, str]]:
    """
    Format messages for Cohere model.
    
    Args:
        messages (List[Message]): List of messages
        
    Returns:
        List[Dict[str, str]]: Formatted messages
    """
    formatted_messages = []
    
    for msg in messages:
        role = "USER" if msg.role == "user" else "CHATBOT" if msg.role == "assistant" else "SYSTEM"
        formatted_messages.append({
            "role": role,
            "message": msg.content
        })
    
    return formatted_messages


def format_messages_for_llama(messages: List[Message]) -> str:
    """
    Format messages for Llama model.
    
    Args:
        messages (List[Message]): List of messages
        
    Returns:
        str: Formatted prompt
    """
    formatted_prompt = ""
    
    for i, msg in enumerate(messages):
        if msg.role == "system":
            formatted_prompt += f"<s>[INST] <<SYS>>\n{msg.content}\n<</SYS>>\n\n"
        elif msg.role == "user":
            if i > 0 and messages[i-1].role == "system":
                formatted_prompt += f"{msg.content} [/INST]\n"
            else:
                formatted_prompt += f"<s>[INST] {msg.content} [/INST]\n"
        elif msg.role == "assistant":
            formatted_prompt += f"{msg.content}</s>\n"
    
    return formatted_prompt
