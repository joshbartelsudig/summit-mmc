# Multi-Model Chat Backend

A FastAPI-based backend service that provides a unified interface for interacting with various AI models from different providers, including Azure OpenAI and Amazon Bedrock.

## Features

- **Multi-Provider Support**
  - Azure OpenAI integration (GPT-3.5, GPT-4)
  - Amazon Bedrock integration (Claude, Llama 2)
  - Extensible architecture for adding new providers

- **Advanced Chat Capabilities**
  - Real-time streaming responses
  - Session management and history
  - Model comparison functionality
  - Model chaining for sequential processing
  - Markdown and code formatting support
  - Customizable system prompts
  - Default and custom prompt handling

- **API Features**
  - RESTful API design
  - Server-Sent Events (SSE) for streaming
  - Comprehensive error handling
  - Rate limiting and request validation
  - Swagger/OpenAPI documentation

## Project Structure

```
backend/
├── app/                    # Main application package
│   ├── api/               # API endpoints
│   │   ├── v1/           # API version 1
│   │   │   ├── chat.py   # Chat endpoints
│   │   │   ├── models.py # Model endpoints
│   │   │   └── compare.py # Comparison endpoints
│   │   └── deps.py       # Dependency injection
│   ├── core/             # Core application components
│   │   ├── config.py     # Configuration management
│   │   ├── security.py   # Security utilities
│   │   └── logging.py    # Logging configuration
│   ├── models/           # Data models
│   │   ├── chat.py       # Chat-related schemas
│   │   └── providers.py  # Provider-specific schemas
│   └── services/         # Business logic
│       ├── azure.py      # Azure OpenAI integration
│       ├── bedrock.py    # AWS Bedrock integration
│       └── chat.py       # Chat processing logic
├── tests/                # Test suite
├── .env.example         # Example environment variables
├── main.py             # Application entry point
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Technical Stack

- **Framework**: FastAPI
- **Python Version**: 3.11+
- **Key Dependencies**:
  - `fastapi`: Web framework
  - `pydantic`: Data validation
  - `uvicorn`: ASGI server
  - `python-dotenv`: Environment management
  - `openai`: Azure OpenAI SDK
  - `boto3`: AWS SDK
  - `aiohttp`: Async HTTP client
  - `pytest`: Testing framework

## Setup & Development

### Prerequisites

- Python 3.11 or higher
- Azure OpenAI subscription (for Azure models)
- AWS account with Bedrock access (for AWS models)
- pip or poetry for package management

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Running the Application

Development server:
```bash
uvicorn main:app --reload --port 8000
```

Production server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
pytest
pytest --cov=app tests/  # With coverage
```

## API Documentation

### Core Endpoints

#### Chat Operations
- `POST /api/v1/chat`
  ```json
  {
    "message": "Your message",
    "model": "gpt-4",
    "session_id": "optional-session-id",
    "system_prompt": "optional-custom-prompt"
  }
  ```

- `POST /api/v1/chat/stream`
  - Streaming version of the chat endpoint
  - Returns Server-Sent Events (SSE)
  - Supports custom system prompts

#### Model Management
- `GET /api/v1/models`
  - Lists available models with capabilities
  - Includes model status and quotas

#### Session Management
- `GET /api/v1/sessions`
  - Retrieves chat history
- `DELETE /api/v1/sessions/{session_id}`
  - Deletes a chat session

#### Model Comparison
- `POST /api/v1/compare`
  ```json
  {
    "prompt": "Your prompt",
    "modelA": "gpt-4",
    "modelB": "claude-v2",
    "system_prompt": "optional-custom-prompt"
  }
  ```
  - Compares responses from multiple models
  - Supports custom system prompts for both models

#### Model Chaining
- `POST /api/v1/chat`
  ```json
  {
    "messages": [
      {"role": "user", "content": "Your message"},
      {"role": "assistant", "content": "First model analysis: ..."}
    ],
    "model": "gpt-4",
    "system_prompt": "custom-system-prompt-for-second-model"
  }
  ```
  - Allows sequential processing through multiple models
  - First model processes the initial user input
  - Second model receives both the original input and the first model's output
  - Supports custom system prompts for each model in the chain

### Environment Variables

#### Azure OpenAI Configuration
- `AZURE_OPENAI_API_KEY` - Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI endpoint URL
- `AZURE_OPENAI_API_VERSION` - API version (default: "2023-05-15")
- `AZURE_OPENAI_DEPLOYED_MODELS` - Comma-separated list of deployed models
- `DEFAULT_SYSTEM_PROMPT` - Default system prompt for all models (optional)

#### AWS Configuration
- `AWS_REGION` - AWS region (default: "us-east-1")
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key

#### Application Settings
- `DEBUG` - Enable debug mode (default: False)
- `LOG_LEVEL` - Logging level (default: "INFO")
- `MAX_TOKENS` - Maximum tokens per request
- `RATE_LIMIT` - Requests per minute per user

## Error Handling

The API uses standard HTTP status codes and returns detailed error messages:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Detailed error message",
    "details": {
      "additional": "information"
    }
  }
}
```

Common error codes:
- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `429`: Too Many Requests
- `500`: Internal Server Error

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and ensure code quality:
   ```bash
   pytest
   flake8
   black .
   ```
5. Submit a pull request

## License

MIT License - see LICENSE file for details
