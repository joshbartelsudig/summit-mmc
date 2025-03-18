"""
Test the utility modules.
"""

import unittest
from app.utils.constants import DEFAULT_MARKDOWN_SYSTEM_PROMPT
from app.utils.chat_formatters import (
    format_code_blocks,
    prepare_messages_with_system_prompt,
    format_messages_for_claude,
    format_messages_for_titan,
    format_messages_for_cohere,
    format_messages_for_llama
)
from app.models.schemas import Message


class TestUtils(unittest.TestCase):
    """Test the utility modules."""
    
    def test_constants(self):
        """Test that constants are defined."""
        self.assertIsNotNone(DEFAULT_MARKDOWN_SYSTEM_PROMPT)
        self.assertTrue(len(DEFAULT_MARKDOWN_SYSTEM_PROMPT) > 0)
        
    def test_format_code_blocks(self):
        """Test code block formatting."""
        # Test opening code block
        content = "```python"
        formatted = format_code_blocks(content)
        self.assertEqual(formatted, "```python\n")
        
        # Test closing code block
        content = "```"
        formatted = format_code_blocks(content)
        self.assertEqual(formatted, "\n```\n")
        
        # Test non-code block
        content = "Hello, world!"
        formatted = format_code_blocks(content)
        self.assertEqual(formatted, "Hello, world!")
        
    def test_prepare_messages(self):
        """Test message preparation."""
        messages = [
            Message(role="user", content="Hello")
        ]
        
        # Test with GPT model
        processed, system = prepare_messages_with_system_prompt(
            messages, 
            system_prompt="Be helpful",
            model="gpt-4"
        )
        self.assertEqual(len(processed), 2)
        self.assertEqual(processed[0].role, "system")
        self.assertEqual(processed[0].content, "Be helpful")
        self.assertIsNone(system)
        
        # Test with Claude model
        processed, system = prepare_messages_with_system_prompt(
            messages, 
            system_prompt="Be helpful",
            model="anthropic.claude-3"
        )
        self.assertEqual(len(processed), 1)
        self.assertEqual(processed[0].role, "user")
        self.assertEqual(system, "Be helpful")
        
    def test_format_messages_for_models(self):
        """Test message formatting for different models."""
        messages = [
            Message(role="system", content="Be helpful"),
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi there")
        ]
        
        # Test Claude formatting
        claude_messages, system = format_messages_for_claude(messages, "Default system")
        self.assertEqual(len(claude_messages), 2)
        self.assertEqual(system, "Be helpful\n\nDefault system")
        
        # Test Titan formatting
        titan_text = format_messages_for_titan(messages)
        self.assertIn("System: Be helpful", titan_text)
        self.assertIn("Human: Hello", titan_text)
        self.assertIn("Assistant: Hi there", titan_text)
        self.assertTrue(titan_text.endswith("Assistant: "))
        
        # Test Cohere formatting
        cohere_messages = format_messages_for_cohere(messages)
        self.assertEqual(len(cohere_messages), 3)
        self.assertEqual(cohere_messages[0]["role"], "SYSTEM")
        self.assertEqual(cohere_messages[1]["role"], "USER")
        self.assertEqual(cohere_messages[2]["role"], "CHATBOT")
        
        # Test Llama formatting
        llama_prompt = format_messages_for_llama(messages)
        self.assertIn("<s>[INST] <<SYS>>", llama_prompt)
        self.assertIn("Be helpful", llama_prompt)
        self.assertIn("<</SYS>>", llama_prompt)
        self.assertIn("Hello [/INST]", llama_prompt)
        self.assertIn("Hi there</s>", llama_prompt)


if __name__ == "__main__":
    unittest.main()
