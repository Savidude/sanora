# Sanora - AI-Powered Finnish Language Tutor

**Sanora** is a conversational Finnish language tutor built with Amazon Bedrock AgentCore. It provides immersive, scenario-based learning experiences for A1-level Finnish learners through natural conversation practice.

## Architecture

### Core Components

```
sanora/
├── agents/              # AI Agent implementations
│   ├── models/         # Agent base classes and configuration
│   ├── prompts/        # System prompts for different AI roles
│   └── tutor_agent.py  # Main AgentCore entrypoint
├── server/             # FastAPI REST API server
│   ├── server.py       # Main FastAPI application
│   ├── config/         # Middleware and logging configuration
│   └── v1/             # API version 1
│       ├── api/        # REST endpoints
│       │   └── chat.py # Chat endpoint implementation
│       ├── models/     # Pydantic data models
│       │   └── agent_comms.py  # Request/Response schemas
│       └── service/    # Business logic layer
│           ├── agent_communication.py  # Agent invocation service
│           └── agent_runtimes.py       # Agent runtime management
```

### AI Agent Pipeline

1. **Teacher Agent** (Gemini 2.5 Flash)
   - Generates conversational responses in Finnish
   - Provides grammar corrections and explanations
   - Creates contextual vocabulary suggestions

2. **Extractor Agent** (GPT-4o)
   - Parses teacher responses into structured JSON
   - Categorizes message types (initiation, feedback, conclusion)
   - Extracts error details and learning metadata

## Quick Start

### Prerequisites

- Python 3.12+
- AWS Account with Bedrock AgentCore access
- OpenAI API key (for Extractor Agent)
- Google Gemini API key (for Teacher Agent)
- AWS CLI configured with appropriate credentials

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd sanora

# Create and activate a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys:
# OPENAI_API_KEY=your_openai_key
# GEMINI_API_KEY=your_gemini_key
# AWS_REGION=eu-central-1
```

### 2. Install Dependencies

```bash
# Ensure virtual environment is activated
# You should see (venv) in your terminal prompt

# Install agent dependencies
cd agents
pip install -r requirements.txt

# Install server dependencies (if separate)
cd ../server
pip install fastapi uvicorn boto3 pydantic
```

### 3. Deploy to AWS

```bash
# Configure AgentCore runtime
agentcore configure -e tutor_agent.py
# Use default values except:
# - Deployment Configuration: Container

# Deploy to AWS
agentcore launch
```

## Usage

### Starting the API Server

```bash

# Run the FastAPI server
python -m server.server

# Server will start on http://localhost:8000
```

### API Endpoints

#### Send Chat Message
```http
POST /api/v1/chat/message
```

**Request Body:**
```json
{
  "message": "Hei! Mitä kuuluu?",
  "sessionId": "user-123"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message_type": "initiation",
    "has_error": "NO",
    "feedback_text": null,
    "error_details": null,
    "greeting": "Hei! Hauska tutustua!",
    "scenario": "You're meeting someone for the first time at a café.",
    "conversation_continuation": "Mitä sinä haluat juoda?",
    "word_tips": [
      {
        "finnish": "juoda",
        "english": "to drink"
      }
    ]
  },
  "session_id": "user-123",
  "timestamp": "2025-11-07T10:30:00.123456"
}
```

### Response Data Models

#### TutorResponseData

| Field | Type | Description |
|-------|------|-------------|
| `message_type` | `MessageType` | Type of message: `initiation`, `feedback`, or `conclusion` |
| `has_error` | `ErrorType` | Error status: `YES`, `NO`, or `MINOR` |
| `feedback_text` | `string \| null` | Feedback provided by the tutor agent |
| `error_details` | `ErrorDetail \| null` | Details about user mistakes and corrections |
| `greeting` | `string \| null` | Greeting message (for initiation messages) |
| `scenario` | `string \| null` | Scenario description (for initiation messages) |
| `conversation_continuation` | `string` | Text to continue the conversation |
| `word_tips` | `WordTip[]` | List of difficult words with translations |

#### ErrorDetail

| Field | Type | Description |
|-------|------|-------------|
| `user_mistake` | `string \| null` | The specific mistake made by the user |
| `corrections` | `string[]` | List of suggested corrections |
| `explanation` | `string \| null` | Explanation of the mistake and corrections |

#### WordTip

| Field | Type | Description |
|-------|------|-------------|
| `finnish` | `string` | The difficult word in Finnish |
| `english` | `string` | The English translation |

### Example cURL Request

```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Minä olen opiskelija",
    "sessionId": "user-123"
  }'
```

### Basic Agent Interaction (Direct)

```python
from agents.models.agent_config import AgentConfig

# Load and create agents
config = AgentConfig("agent_config.json")
teacher = config.create_agent("teacher_agent")

# Start Finnish conversation
response = teacher.process("Hei! Mitä kuuluu?")
print(response.content[0].text)
```

### Extending AI Models

```python
# Add support for new AI providers
from agents.models.base_agent import BaseAgent, AgentFactory

# Create custom agent
custom_agent = AgentFactory.create_agent_from_config({
    "prompt_path": "path/to/prompt.txt",
    "model_type": "your_provider",
    "model_id": "your_model",
    "agent_type": "text"
})
```

### Interactive API Documentation

Once the server is running, access the auto-generated API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive API exploration and testing capabilities.

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for Extractor Agent | Yes |
| `GEMINI_API_KEY` | Google Gemini API key for Teacher Agent | Yes |
| `AWS_REGION` | AWS region for Bedrock AgentCore | Yes (default: eu-central-1) |
| `AWS_ACCESS_KEY_ID` | AWS access key | Yes |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | Yes |

### Agent Configuration

Agent configuration is managed in `agents/agent_config.json`:

```json
{
  "teacher_agent": {
    "prompt_path": "prompts/prompt_tutor_finnish.txt",
    "model_type": "gemini",
    "model_id": "gemini-2.5-flash",
    "agent_type": "text"
  },
  "extractor_agent": {
    "prompt_path": "prompts/prompt_agent_extractor.txt",
    "model_type": "openai",
    "model_id": "gpt-4o",
    "agent_type": "text"
  }
}
```

## Testing

### Testing the API Server

```bash
# Start the server
cd server
python -u server.py

# Test health endpoint
curl http://localhost:8000/health

# Test chat endpoint
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hei! Mitä kuuluu?",
    "sessionId": "test-session-1"
  }'
```

### Local Testing with Strands Agents

```bash
cd agents
python -u tutor_agent.py
```

Send POST requests to `http://localhost:8080/invocations`:

```json
{
  "prompt": "Hei! Mitä kuuluu?"
}
```

### Testing with AgentCore CLI

```bash
agentcore invoke '{"prompt": "Hei! Mitä kuuluu?"}'
```

**Tervetuloa opiskelemaan suomea! (Welcome to learning Finnish!)** 🇫🇮
