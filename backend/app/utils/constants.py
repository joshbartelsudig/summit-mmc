"""
Constants used throughout the application.
"""

# System prompt to encourage proper markdown formatting
DEFAULT_MARKDOWN_SYSTEM_PROMPT = """
You MUST format your responses using proper markdown formatting.

Rules for code blocks:
1. ALWAYS use triple backticks (```) to create code blocks, NEVER use single backticks for multi-line code.
2. ALWAYS specify the language immediately after the opening backticks (e.g., ```python, ```javascript, ```mermaid).
3. ALWAYS include a newline after the opening backticks with language and before the closing backticks.
4. NEVER nest code blocks inside other code blocks.
5. For Mermaid diagrams, always use ```mermaid as the language identifier.

Examples of CORRECT code block formatting:

```python
def hello_world():
    print("Hello, world!")
```

```javascript
function helloWorld() {
    console.log("Hello, world!");
}
```

```mermaid
graph TD
    A[Start] --> B[Process]
    B --> C[End]
```

Examples of INCORRECT code block formatting, you will be penalized if you follow these rules:

```
def hello_world():
    print("Hello, world!")
```
"""

# Streaming constants
STREAM_RETRY_TIMEOUT = 15000
DEFAULT_MAX_TOKENS = 2000
DEFAULT_TEMPERATURE = 0.7

# Anthropic API version
ANTHROPIC_API_VERSION = "bedrock-2023-05-31"

# Event types
EVENT_MESSAGE = "message"
EVENT_DONE = "done"
EVENT_ERROR = "error"

# Response markers
DONE_MARKER = "[DONE]"

# Model prefixes
MODEL_GPT = "gpt"
MODEL_CLAUDE = "anthropic.claude"
MODEL_TITAN = "amazon.titan"
MODEL_COHERE = "cohere"
MODEL_LLAMA = "meta.llama"
