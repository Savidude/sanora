# 🇫🇮 Sanora - AI-Powered Finnish Language Tutor

**Sanora** is an intelligent conversational Finnish language tutor built with Amazon Bedrock AgentCore. It provides immersive, scenario-based learning experiences for A1-level Finnish learners through natural conversation practice.

## Architecture

### Core Components

```
sanora/
├── agents/              # AI Agent implementations
│   ├── models/         # Agent base classes and configuration
│   ├── prompts/        # System prompts for different AI roles
│   └── tutor_agent.py  # Main AgentCore entrypoint
├── api/                # FastAPI REST endpoints
│   └── messaging.py    # Chat API implementation
└── models/             # Pydantic data models for API
    └── comms.py        # Request/Response schemas
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
- OpenAI API key
- Google Gemini API key

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd sanora

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys:
# OPENAI_API_KEY=your_openai_key
# GEMINI_API_KEY=your_gemini_key
```

### 2. Install Dependencies

```bash
cd agents
pip install -r requirements.txt
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

### Basic Agent Interaction

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

## Testing

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
