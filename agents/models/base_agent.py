"""Base agent class for creating generic agents with different models and prompts."""

import json
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Union, List

import boto3
from botocore.exceptions import ClientError

from strands import Agent
from strands.agent.agent_result import AgentResult
from strands.types.content import Message, ContentBlock
from strands.models.openai import OpenAIModel
from strands.models.gemini import GeminiModel


def get_api_key_from_secret(key_name: str, secret_name: str = "AgentKeys") -> str:
    """
    Retrieve an API key from AWS Secrets Manager.

    Args:
        key_name: The name of the key within the secret (e.g., 'OpenAIApiKey' or 'GeminiApiKey')
        secret_name: The name of the secret in AWS Secrets Manager (default: 'AgentKeys')

    Returns:
        str: The API key value

    Raises:
        ClientError: If the secret cannot be retrieved
        KeyError: If the key is not found in the secret
    """
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager")

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret_string = get_secret_value_response["SecretString"]
        secret_dict = json.loads(secret_string)
        return secret_dict[key_name]
    except ClientError as e:
        raise e
    except KeyError as exc:
        raise KeyError(f"Key '{key_name}' not found in secret '{secret_name}'") from exc


class ModelType(str, Enum):
    """Supported model types."""

    OPENAI = "openai"
    GEMINI = "gemini"


class OpenAIModelId(str, Enum):
    """Supported OpenAI model IDs."""

    GPT_4O = "gpt-4o"


class GeminiModelId(str, Enum):
    """Supported Gemini model IDs."""

    GEMINI_2_5_FLASH = "gemini-2.5-flash"


class AgentType(str, Enum):
    """Supported agent types."""

    TEXT = "text"
    CONTENT = "content"


class BaseAgent(ABC):
    """Abstract base class for creating agents with different models and prompts."""

    def __init__(
        self,
        prompt_path: Union[str, Path],
        model_config: Dict[str, Any],
        model_type: ModelType = ModelType.OPENAI,
    ):
        """
        Initialize the base agent.

        Args:
            prompt_path: Path to the prompt file
            model_config: Configuration for the model including model_id and client_args
            model_type: Type of model to use (ModelType enum)
        """
        self.prompt_path = Path(prompt_path)
        self.model_config = model_config
        self.model_type = model_type

        self.prompt = self._load_prompt()
        self.model = self._create_model()
        self.agent = Agent(model=self.model, system_prompt=self.prompt)

    def _load_prompt(self) -> str:
        """Load the prompt from the specified file."""

        return self.prompt_path.read_text(encoding="utf-8")

    def _create_model(self):
        """Create the appropriate model based on model_type."""

        if self.model_type == ModelType.OPENAI:
            return OpenAIModel(**self.model_config)
        elif self.model_type == ModelType.GEMINI:
            return GeminiModel(**self.model_config)
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")

    @abstractmethod
    def process(self, input_data: Union[str, List[ContentBlock]]) -> Message:
        """
        Process input and return response.

        Args:
            input_data: Input to process (string or content blocks)

        Returns:
            Message: The agent's response
        """
        raise NotImplementedError("Subclasses must implement the process method")

    def _get_response(self, input_data: Union[str, List[ContentBlock]]) -> AgentResult:
        """Get response from the agent."""
        return self.agent(input_data)


class TextAgent(BaseAgent):
    """Generic agent for processing text input."""

    def process(self, input_data: str) -> Message:
        """
        Process text input and return response.

        Args:
            input_data: Text input to process

        Returns:
            Message: The agent's response
        """
        response: AgentResult = self._get_response(input_data)
        return response.message


class ContentAgent(BaseAgent):
    """Generic agent for processing content blocks."""

    def process(self, input_data: Message) -> Message:
        """
        Process content blocks and return response.

        Args:
            input_data: message content blocks to process

        Returns:
            Message: The agent's response
        """
        response: AgentResult = self._get_response(input_data["content"])
        return response.message


class AgentFactory:
    """Factory class for creating different types of agents."""

    @staticmethod
    def create_openai_agent(
        prompt_path: Union[str, Path],
        model_id: OpenAIModelId = OpenAIModelId.GPT_4O,
        api_key: str = None,
        agent_type: AgentType = AgentType.TEXT,
    ) -> BaseAgent:
        """
        Create an OpenAI-based agent.

        Args:
            prompt_path: Path to the prompt file
            model_id: OpenAI model ID (OpenAIModelId enum)
            api_key: OpenAI API key (if None, retrieves from AWS Secrets Manager)
            agent_type: Type of agent (AgentType enum)

        Returns:
            BaseAgent: Configured agent instance
        """
        if api_key is None:
            try:
                api_key = get_api_key_from_secret("OpenAIApiKey")
            except (ClientError, KeyError) as e:
                raise ValueError(
                    f"OpenAI API key not found in parameters or AWS Secrets Manager: {e}"
                ) from e

        model_config = {
            "client_args": {
                "api_key": api_key,
            },
            "model_id": model_id.value,
        }

        if agent_type == AgentType.TEXT:
            return TextAgent(prompt_path, model_config, ModelType.OPENAI)
        elif agent_type == AgentType.CONTENT:
            return ContentAgent(prompt_path, model_config, ModelType.OPENAI)
        else:
            raise ValueError(f"Unsupported agent type: {agent_type}")

    @staticmethod
    def create_gemini_agent(
        prompt_path: Union[str, Path],
        model_id: GeminiModelId = GeminiModelId.GEMINI_2_5_FLASH,
        api_key: str = None,
        agent_type: AgentType = AgentType.TEXT,
    ) -> BaseAgent:
        """
        Create a Gemini-based agent.

        Args:
            prompt_path: Path to the prompt file
            model_id: Gemini model ID (GeminiModelId enum)
            api_key: Gemini API key (if None, retrieves from AWS Secrets Manager)
            agent_type: Type of agent (AgentType enum)

        Returns:
            BaseAgent: Configured agent instance
        """
        if api_key is None:
            try:
                api_key = get_api_key_from_secret("GeminiApiKey")
            except (ClientError, KeyError) as e:
                raise ValueError(
                    f"Gemini API key not found in parameters or AWS Secrets Manager: {e}"
                ) from e

        model_config = {
            "client_args": {
                "api_key": api_key,
            },
            "model_id": model_id.value,
        }

        if agent_type == AgentType.TEXT:
            return TextAgent(prompt_path, model_config, ModelType.GEMINI)
        elif agent_type == AgentType.CONTENT:
            return ContentAgent(prompt_path, model_config, ModelType.GEMINI)
        else:
            raise ValueError(f"Unsupported agent type: {agent_type}")

    @staticmethod
    def create_agent_from_config(config: Dict[str, str]) -> BaseAgent:
        """
        Create an agent from a configuration dictionary.

        Args:
            config: Configuration dictionary with keys:
                - prompt_path: Path to prompt file
                - model_type: "openai" or "gemini" (string)
                - model_id: Model ID (string)
                - api_key: API key (optional)
                - agent_type: "text" or "content" (string)

        Returns:
            BaseAgent: Configured agent instance
        """
        model_type = ModelType(config.get("model_type"))
        agent_type = AgentType(config.get("agent_type"))

        if model_type == ModelType.OPENAI:
            model_id = OpenAIModelId(config.get("model_id", "gpt-4o"))

            return AgentFactory.create_openai_agent(
                prompt_path=config["prompt_path"],
                model_id=model_id,
                api_key=config.get("api_key"),
                agent_type=agent_type,
            )
        elif model_type == ModelType.GEMINI:
            model_id_str = config.get("model_id", "gemini-2.5-flash")
            model_id_enum = GeminiModelId(model_id_str)

            return AgentFactory.create_gemini_agent(
                prompt_path=config["prompt_path"],
                model_id=model_id_enum,
                api_key=config.get("api_key"),
                agent_type=agent_type,
            )
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
