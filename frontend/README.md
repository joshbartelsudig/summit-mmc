# Multi-Model Chat Frontend

A Next.js-based chat interface for interacting with multiple AI models, allowing users to chat with and compare responses from different language models.

## Features

- **Multi-Model Chat Interface**
  - Real-time chat with AI models
  - Support for multiple model providers (Azure OpenAI, Amazon Bedrock)
  - Dynamic model selection
  - Custom system prompts for model behavior
  - Markdown rendering with syntax highlighting
  - Code block formatting with language detection

- **Model Comparison**
  - Side-by-side model response comparison
  - Simultaneous prompting of two models
  - Easy model switching and selection
  - Customizable system prompts per model

- **Model Chaining**
  - Sequential processing through multiple models
  - Configurable system prompts for each model in the chain
  - Visualization of intermediate and final results
  - Tabbed interface for configuration and results

- **User Experience**
  - Responsive design for all screen sizes
  - Dark/Light theme support
  - Chat history management
  - Real-time message streaming
  - Clean and modern UI using shadcn/ui components

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **Code Highlighting**: Highlight.js
- **Markdown Processing**: React-Markdown with remark-gfm

## Project Structure

```
src/
├── app/                    # Next.js app router pages
│   ├── compare/           # Model comparison page
│   ├── chain/             # Model chaining page
│   └── page.tsx           # Main chat interface
├── components/            # React components
│   ├── chat-history.tsx   # Chat session management component
│   ├── chat-message.tsx   # Individual message display component
│   ├── markdown-renderer.tsx # Markdown rendering with code highlighting
│   ├── model-selector.tsx # Model selection dropdown
│   └── ui/                # UI components from shadcn/ui
├── services/              # Service layer
│   └── api.ts             # Centralized API service for backend communication
├── lib/                   # Utility functions
└── types/                 # TypeScript type definitions
```

## API Service

The application uses a centralized API service (`src/services/api.ts`) to handle all backend communication. This service provides methods for:

- Fetching chat sessions
- Creating new sessions
- Updating session titles
- Deleting sessions
- Sending messages and receiving responses

Example usage:

```typescript
// Fetch all sessions
const sessions = await apiService.getSessions();

// Create a new session
const newSession = await apiService.createSession('New Chat');

// Send a message
const response = await apiService.sendMessage(
  messages,
  modelId,
  systemPrompt,
  sessionId,
  streamingEnabled
);
```

## Session Management

Chat sessions are managed through a combination of local state and backend persistence. The application:

1. Fetches existing sessions on component mount
2. Creates new sessions when requested
3. Updates session titles based on the first user message
4. Deletes sessions when requested
5. Loads messages for the selected session

Sessions are stored in Redis on the backend and include:
- Session ID
- Title
- Creation date
- Last updated timestamp
- Preview of the conversation
- Messages

## Setup & Development

### Prerequisites

- Node.js 18.17 or later
- npm or pnpm

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   cd frontend
   npm install
   # or
   pnpm install
   ```
3. Create a `.env.local` file with required environment variables:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

### Development Server

```bash
npm run dev
# or
pnpm dev
```

The application will be available at [http://localhost:3000](http://localhost:3000).

## API Integration

The frontend communicates with a backend API that provides model interaction and chat functionality. All endpoints expect and return JSON data unless otherwise specified.

### Endpoints

#### Model Management
- `GET /api/v1/models`
  - Retrieves available models
  - Response: Array of model information including name, provider, and capabilities

#### Chat Operations
- `POST /api/v1/chat`
  - Initiates a new chat message
  - Body: `{ message: string, model: string, sessionId?: string, system_prompt?: string }`
  - Response: Complete message response

- `POST /api/v1/chat/stream`
  - Streams chat responses in real-time
  - Body: Same as `/chat`
  - Response: Server-Sent Events (SSE) stream
  - Stream format:
    ```typescript
    {
      type: "content" | "error"
      content?: string    // For content updates
      error?: string     // For error messages
      done: boolean      // Indicates stream completion
    }
    ```

#### Session Management
- `GET /api/v1/sessions`
  - Retrieves chat history
  - Response: Array of chat sessions with messages

- `DELETE /api/v1/sessions/:id`
  - Deletes a chat session
  - Response: Success confirmation

#### Model Comparison
- `POST /api/v1/compare`
  - Compares responses from two models
  - Body: `{ prompt: string, modelA: string, modelB: string, system_prompt?: string }`
  - Response: Streamed responses from both models

### Error Handling

The API uses standard HTTP status codes:
- 200: Success
- 400: Bad Request (invalid parameters)
- 401: Unauthorized
- 404: Resource Not Found
- 500: Server Error

Error responses follow the format:
```json
{
  "error": {
    "message": "Error description",
    "code": "ERROR_CODE"
  }
}
```

### Example Usage

```typescript
// Streaming chat example
const response = await fetch('/api/v1/chat/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: "Your prompt here",
    model: "gpt-4",
    sessionId: "optional-session-id",
    system_prompt: "optional-system-prompt"
  })
});

const reader = response.body?.getReader();
while (reader) {
  const { value, done } = await reader.read();
  if (done) break;
  // Process streamed response
}
```

Refer to the backend documentation for detailed API specifications and authentication requirements.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and ensure code quality:
   ```bash
   npm run lint
   npm run test
   ```
5. Submit a pull request

## License

MIT License - see LICENSE file for details
