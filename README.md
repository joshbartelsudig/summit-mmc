# Multi-Model Chat (MMC)

A modern web application that provides a unified interface for interacting with multiple AI language models from various providers. Compare responses, manage chat sessions, and leverage the unique capabilities of different AI models through a single, intuitive interface.

## 🌟 Features

- **Multi-Model Support**
  - Azure OpenAI models (GPT-3.5, GPT-4)
  - Amazon Bedrock models (Claude, Llama 2)
  - Real-time streaming responses
  - Side-by-side model comparison
  - Model chaining for sequential processing
  - Custom system prompts for each chat
  - Optimized compare page layout with space-efficient design
  - Fullscreen toggle for individual model responses
  - One-click copy functionality for model outputs
  - Recommended model pairings for quick comparison setup
  - Categorized prompt templates for different use cases

- **Modern Web Interface**
  - Clean, responsive design
  - Real-time streaming updates
  - Code syntax highlighting
  - Markdown rendering with Mermaid diagrams
  - Dark/light mode support

- **Session Management**
  - Persistent chat history
  - Multiple concurrent sessions
  - Session export/import

## 🏗️ Architecture

The application consists of two main components:

- **[Frontend](frontend/README.md)**: Next.js 14 application with TypeScript and Tailwind CSS
- **[Backend](backend/README.md)**: FastAPI service managing model interactions and sessions

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Azure OpenAI subscription
- AWS account with Bedrock access

### Cloud Provider Setup

#### Azure OpenAI Setup

1. **Create an Azure Account**
   - Visit [Azure Portal](https://portal.azure.com)
   - Sign up for an account if you don't have one
   - Navigate to Azure OpenAI service

2. **Request Access**
   - Apply for access to Azure OpenAI service
   - This may take 1-2 business days for approval

3. **Create a Resource**
   - Create a new Azure OpenAI resource
   - Select your subscription and resource group
   - Choose a region where Azure OpenAI is available
   - Note down the resource name

4. **Deploy Models**
   - In Azure OpenAI Studio, deploy your desired models
   - Common deployments:
     - GPT-3.5-Turbo
     - GPT-4
   - Note down the deployment names

5. **Get Credentials**
   - Find your API key in "Keys and Endpoint"
   - Copy the endpoint URL
   - These will be used in your `.env` file

#### AWS Bedrock Setup

1. **Create an AWS Account**
   - Visit [AWS Console](https://aws.amazon.com)
   - Create a new account if needed

2. **Request Bedrock Access**
   - Navigate to Amazon Bedrock console
   - Request access to the service
   - Request access to specific models (Claude, Llama 2)

3. **Create IAM User**
   - Go to IAM service
   - Create a new user with programmatic access
   - Attach the `AmazonBedrockFullAccess` policy
   - Save the access key ID and secret key

4. **Enable Models**
   - In Bedrock console, go to Model access
   - Enable the models you want to use
   - Wait for approval if required

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd MMC
   ```

2. Set up the backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   ```

3. Set up the frontend:
   ```bash
   cd ../frontend
   npm install
   cp .env.example .env.local
   ```

4. Configure environment variables:
   - Backend `.env`:
     ```env
     # Azure OpenAI
     AZURE_OPENAI_API_KEY=your-api-key
     AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
     AZURE_OPENAI_API_VERSION=2023-05-15
     AZURE_OPENAI_DEPLOYED_MODELS=gpt-35-turbo,gpt-4

     # AWS Bedrock
     AWS_ACCESS_KEY_ID=your-access-key
     AWS_SECRET_ACCESS_KEY=your-secret-key
     AWS_REGION=us-east-1
     ```

   - Frontend `.env.local`:
     ```env
     NEXT_PUBLIC_API_URL=http://localhost:8000
     ```

### Running the Application

1. Start the backend:
   ```bash
   cd backend
   uvicorn main:app --reload --port 8000
   ```

2. Start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

## 📚 Documentation

- [Frontend Documentation](frontend/README.md)
  - UI components
  - State management
  - API integration
  - Styling

- [Backend Documentation](backend/README.md)
  - API endpoints
  - Model integration
  - Session management
  - Error handling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

See [Contributing Guidelines](CONTRIBUTING.md) for more details.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details
