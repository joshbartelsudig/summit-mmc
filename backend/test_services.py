"""
Test the service modules.
"""

import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import json

from app.models.schemas import Message, ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.services.formatter_service import FormatterService


class TestFormatterService(unittest.TestCase):
    """Test the formatter service."""
    
    def test_get_model_type(self):
        """Test getting model type."""
        self.assertEqual(FormatterService.get_model_type("gpt-4"), "gpt")
        self.assertEqual(FormatterService.get_model_type("anthropic.claude-3"), "anthropic.claude")
        self.assertEqual(FormatterService.get_model_type("amazon.titan"), "amazon.titan")
        self.assertEqual(FormatterService.get_model_type("cohere.command"), "cohere")
        self.assertEqual(FormatterService.get_model_type("meta.llama"), "meta.llama")
        self.assertEqual(FormatterService.get_model_type("unknown"), "unknown")
    
    async def test_format_streaming_chunk(self):
        """Test formatting streaming chunk."""
        chunk = await FormatterService.format_streaming_chunk("Hello, world!")
        self.assertEqual(chunk["event"], "message")
        self.assertTrue("id" in chunk)
        self.assertEqual(chunk["retry"], 15000)
        
        data = json.loads(chunk["data"])
        self.assertEqual(data["content"], "Hello, world!")
    
    async def test_format_done_event(self):
        """Test formatting done event."""
        event = await FormatterService.format_done_event()
        self.assertEqual(event["event"], "done")
        
        data = json.loads(event["data"])
        self.assertEqual(data["content"], "[DONE]")
    
    async def test_format_error_event(self):
        """Test formatting error event."""
        error = Exception("Test error")
        event = await FormatterService.format_error_event(error)
        self.assertEqual(event["event"], "error")
        
        data = json.loads(event["data"])
        self.assertEqual(data["error"], "Streaming error: Test error")
    
    def test_format_messages_for_api(self):
        """Test formatting messages for API."""
        messages = [
            Message(role="system", content="Be helpful"),
            Message(role="user", content="Hello")
        ]
        
        # Test GPT format
        gpt_messages = FormatterService.format_messages_for_api(messages, "gpt")
        self.assertEqual(len(gpt_messages), 2)
        self.assertEqual(gpt_messages[0]["role"], "system")
        self.assertEqual(gpt_messages[0]["content"], "Be helpful")
        
        # Test Claude format
        claude_messages = FormatterService.format_messages_for_api(messages, "anthropic.claude")
        self.assertEqual(len(claude_messages), 2)
        self.assertEqual(claude_messages[0]["role"], "system")
        self.assertEqual(claude_messages[0]["content"][0]["type"], "text")
        self.assertEqual(claude_messages[0]["content"][0]["text"], "Be helpful")


class TestChatService(unittest.TestCase):
    """Test the chat service."""
    
    @patch('app.services.model_router.model_router.route_chat_completion')
    async def test_generate_chat_completion(self, mock_route):
        """Test generating chat completion."""
        # Mock the route_chat_completion method
        mock_route.return_value = AsyncMock(return_value={
            "choices": [
                {
                    "message": {"content": "Hello, world!"},
                    "finish_reason": "stop"
                }
            ]
        })
        
        # Create a chat request
        request = ChatRequest(
            model="gpt-4",
            messages=[Message(role="user", content="Hello")],
            stream=False
        )
        
        # Generate chat completion
        response = await ChatService.generate_chat_completion(request)
        
        # Check response
        self.assertIsInstance(response, ChatResponse)
        self.assertEqual(response.model, "gpt-4")
        self.assertEqual(len(response.choices), 1)
        self.assertEqual(response.choices[0].message.role, "assistant")
        self.assertEqual(response.choices[0].message.content, "Hello, world!")
        self.assertEqual(response.choices[0].finish_reason, "stop")
    
    def test_prepare_requests(self):
        """Test preparing requests for different models."""
        messages = [
            Message(role="system", content="Be helpful"),
            Message(role="user", content="Hello")
        ]
        
        # Test Azure request
        azure_request = ChatService.prepare_azure_request(messages, "gpt-4")
        self.assertEqual(azure_request["model"], "gpt-4")
        self.assertEqual(len(azure_request["messages"]), 2)
        self.assertTrue(azure_request["stream"])
        
        # Test Claude request
        claude_request = ChatService.prepare_claude_request(messages, "Be helpful")
        self.assertEqual(claude_request["anthropic_version"], "bedrock-2023-05-31")
        self.assertEqual(claude_request["max_tokens"], 2000)
        self.assertEqual(claude_request["system"], "Be helpful\n\nBe helpful")
        
        # Test Titan request
        titan_request = ChatService.prepare_titan_request(messages)
        self.assertIn("System: Be helpful", titan_request)
        self.assertIn("Human: Hello", titan_request)
        
        # Test Cohere request
        cohere_request = ChatService.prepare_cohere_request(messages)
        self.assertEqual(len(cohere_request), 2)
        self.assertEqual(cohere_request[0]["role"], "SYSTEM")
        
        # Test Llama request
        llama_request = ChatService.prepare_llama_request(messages)
        self.assertIn("<s>[INST] <<SYS>>", llama_request)
        self.assertIn("Be helpful", llama_request)


if __name__ == "__main__":
    unittest.main()
