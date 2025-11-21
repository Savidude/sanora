# Running Sanora Tutor Agent Locally with Strands Agents

This guide explains how to run the Finnish tutor agent (`tutor_agent.py`) locally using Strands Agents for development and testing purposes.

## Overview

The tutor agent is built using the Strands Agents framework and consists of two AI agents working in sequence:

1. **Teacher Agent** (Gemini 2.5 Flash): Generates conversational responses in Finnish with grammar corrections and vocabulary suggestions
2. **Extractor Agent** (GPT-4o): Parses the teacher's response into structured JSON format

## Prerequisites

- Python 3.12+
- OpenAI API key (for Extractor Agent)
- Google Gemini API key (for Teacher Agent)
- Virtual environment (recommended)

## Setup Instructions

### 1. Create and Activate Virtual Environment

```bash
# Navigate to the agents directory
cd agents

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows

# Verify activation (you should see (venv) in your prompt)
```

### 2. Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

Key dependencies include:
- `strands-agents==1.15.0` - Core framework for building AI agents
- `openai==1.109.1` - OpenAI API client
- `google-genai==1.49.0` - Google Gemini API client
- `python-dotenv==1.2.1` - Environment variable management

### 3. Configure Environment Variables

Create a `.env` file in the `agents` directory:

```bash
# Create .env file
touch .env
```

Add your API keys to the `.env` file:

```env
OpenAIApiKey=your_openai_api_key_here
GeminiApiKey=your_gemini_api_key_here
```

**Important Notes:**
- Replace `your_openai_api_key_here` with your actual OpenAI API key
- Replace `your_gemini_api_key_here` with your actual Google Gemini API key
- The `.env` file should be in the same directory as `tutor_agent.py`
- Never commit your `.env` file to version control

### 4. Verify Configuration Files

Ensure the following files are present in the `agents` directory:

```
agents/
├── tutor_agent.py              # Main agent entrypoint
├── agent_config.json            # Agent configuration
├── .env                         # API keys (you created this)
├── requirements.txt             # Python dependencies
├── models/
│   ├── base_agent.py           # Agent base classes
│   └── agent_config.py         # Configuration loader
└── prompts/
    ├── prompt_tutor_finnish.txt    # Teacher agent prompt
    └── prompt_agent_extractor.txt  # Extractor agent prompt
```

## Running the Agent Locally

Run the agent as a Python script:

```bash
# Ensure you're in the agents directory and venv is activated
python -u tutor_agent.py
```

This will start the agent server. By default, it runs on `http://localhost:8080`.

## Testing the Agent

### Using cURL

Once the agent is running, test it with cURL:

```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hei! Mitä kuuluu?"}'
```

### Sample Request and Response

**Request:**
```json
{
  "prompt": "Hei! Minä olen opiskelija"
}
```

**Response:**
```json
{
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "{\"message_type\": \"feedback\", \"has_error\": \"MINOR\", \"feedback_text\": \"Almost perfect! A minor correction...\", ...}"
    }
  ]
}
```

The response contains structured JSON with:
- `message_type`: Type of message (`initiation`, `feedback`, or `conclusion`)
- `has_error`: Error status (`YES`, `NO`, or `MINOR`)
- `feedback_text`: Feedback on user's Finnish
- `error_details`: Corrections and explanations
- `conversation_continuation`: Next conversational turn
- `word_tips`: Vocabulary suggestions with translations

## Understanding the Agent Architecture

### Agent Flow

```
User Input (Finnish text)
    ↓
Teacher Agent (Gemini 2.5 Flash)
    - Generates conversational response
    - Provides grammar corrections
    - Suggests vocabulary
    ↓
Extractor Agent (GPT-4o)
    - Parses teacher response
    - Structures into JSON format
    - Categorizes message types
    ↓
Structured JSON Response
```

### Configuration (`agent_config.json`)

The agent configuration specifies:

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
    "agent_type": "content"
  }
}
```

### Agent Types

- **TextAgent**: Processes plain text input (used by Teacher Agent)
- **ContentAgent**: Processes structured content blocks (used by Extractor Agent)

## Customization

### Changing AI Models

Edit `agent_config.json` to use different models:

```json
{
  "teacher_agent": {
    "model_type": "openai",
    "model_id": "gpt-4o",
    ...
  }
}
```

Supported models:
- **OpenAI**: `gpt-4o`
- **Gemini**: `gemini-2.5-flash`

### Modifying Prompts

Edit the prompt files in the `prompts/` directory:
- `prompt_tutor_finnish.txt` - Controls teacher agent behavior
- `prompt_agent_extractor.txt` - Controls JSON extraction format

### Using Custom API Keys in Code

For testing without AWS Secrets Manager, modify the agent creation:

```python
from models.base_agent import AgentFactory, AgentType, OpenAIModelId, GeminiModelId

# Create agents with explicit API keys
teacher = AgentFactory.create_gemini_agent(
    prompt_path="prompts/prompt_tutor_finnish.txt",
    model_id=GeminiModelId.GEMINI_2_5_FLASH,
    api_key="your_gemini_api_key",
    agent_type=AgentType.TEXT
)

extractor = AgentFactory.create_openai_agent(
    prompt_path="prompts/prompt_agent_extractor.txt",
    model_id=OpenAIModelId.GPT_4O,
    api_key="your_openai_api_key",
    agent_type=AgentType.CONTENT
)
```

### Logging

The agent uses Python's logging module. To increase verbosity:

```python
# In tutor_agent.py, change:
logging.basicConfig(level=logging.DEBUG)  # Change INFO to DEBUG
```

## Development Workflow

### Interactive Testing

```bash
# Terminal 1: Start the agent
cd agents
source venv/bin/activate
python tutor_agent.py

# Terminal 2: Test with different inputs
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hei! Kuinka voin auttaa?"}'
```

### Code Modifications

1. Make changes to `tutor_agent.py` or related files
2. Stop the agent (Ctrl+C)
3. Restart: `python tutor_agent.py`
4. Test your changes

### Adding New Agents

1. Define agent in `agent_config.json`:
```json
{
  "my_agent": {
    "prompt_path": "prompts/my_prompt.txt",
    "model_type": "openai",
    "model_id": "gpt-4o",
    "agent_type": "text"
  }
}
```

2. Load in `tutor_agent.py`:
```python
tutors = config.create_all_agents()
my_agent = tutors["my_agent"]
```

## Next Steps

- **Production Deployment**: See main project README for AWS AgentCore deployment
- **Integration**: Connect to the FastAPI server in `deployment-stacks/lambdas/server/`
- **Monitoring**: Add custom logging and metrics
- **Testing**: Create unit tests for agent behavior

## Resources

- [Strands Agents Documentation](https://docs.strands.ai/)
- [OpenAI API Reference](https://platform.openai.com/docs)
- [Google Gemini API Docs](https://ai.google.dev/docs)
- [Python dotenv Guide](https://pypi.org/project/python-dotenv/)

