"""Base agent class for creating generic agents with different models and prompts."""

import logging
import os
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

logger = logging.getLogger(__name__)


def get_api_key(secret_name: str) -> str:
    """
    Retrieve an API key from environment variable or AWS Secrets Manager.

    Args:
        secret_name: The name of the secret. First checks for an environment variable
                    with this name, then falls back to AWS Secrets Manager.

    Returns:
        str: The API key value

    Raises:
        ClientError: If the secret cannot be retrieved from AWS Secrets Manager
        ValueError: If the secret is not found in environment or AWS Secrets Manager
    """
    # First check if environment variable exists
    env_value = os.getenv(secret_name)
    if env_value:
        logger.info("Retrieved API key '%s' from environment variable", secret_name)
        return env_value
    
    # Fall back to AWS Secrets Manager
    logger.info("Environment variable '%s' not found, checking AWS Secrets Manager", secret_name)
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager")

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret_string = get_secret_value_response["SecretString"]
        logger.info("Retrieved API key '%s' from AWS Secrets Manager", secret_name)
        return secret_string
    except ClientError as e:
        logger.error("Failed to retrieve secret '%s': %s", secret_name, str(e))
        raise e


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
        logger.info(
            "Initializing %s with model type: %s",
            self.__class__.__name__,
            model_type.value,
        )
        self.prompt_path = Path(prompt_path)
        self.model_config = model_config
        self.model_type = model_type

        self.prompt = self._load_prompt()
        self.model = self._create_model()
        self.agent = Agent(model=self.model, system_prompt=self.prompt)
        logger.info("%s initialized successfully", self.__class__.__name__)

    def _load_prompt(self) -> str:
        """Load the prompt from the specified file."""
        logger.debug("Loading prompt from: %s", self.prompt_path)
        try:
            prompt = self.prompt_path.read_text(encoding="utf-8")
            logger.debug("Loaded prompt with %d characters", len(prompt))
            return prompt
        except Exception as e:
            logger.error("Failed to load prompt from %s: %s", self.prompt_path, str(e))
            raise

    def _create_model(self):
        """Create the appropriate model based on model_type."""
        logger.debug("Creating model of type: %s", self.model_type.value)

        try:
            if self.model_type == ModelType.OPENAI:
                model_id = self.model_config.get("model_id", "unknown")
                logger.info("Creating OpenAI model: %s", model_id)
                return OpenAIModel(**self.model_config)
            elif self.model_type == ModelType.GEMINI:
                model_id = self.model_config.get("model_id", "unknown")
                logger.info("Creating Gemini model: %s", model_id)
                return GeminiModel(**self.model_config)
            else:
                logger.error("Unsupported model type: %s", self.model_type)
                raise ValueError(f"Unsupported model type: {self.model_type}")
        except Exception as e:
            logger.error("Failed to create model: %s", str(e), exc_info=True)
            raise

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
        logger.info("TextAgent processing input of length: %d", len(input_data))
        try:
            response: AgentResult = self._get_response(input_data)
            logger.info("TextAgent successfully processed input")
            return response.message
        except Exception as e:
            logger.error("TextAgent failed to process input: %s", str(e), exc_info=True)
            raise


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
        logger.info("ContentAgent processing message content")
        try:
            response: AgentResult = self._get_response(input_data["content"])
            logger.info("ContentAgent successfully processed content")
            return response.message
        except Exception as e:
            logger.error(
                "ContentAgent failed to process content: %s", str(e), exc_info=True
            )
            raise


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
        logger.info(
            "Creating OpenAI agent: model=%s, agent_type=%s",
            model_id.value,
            agent_type.value,
        )

        if api_key is None:
            try:
                api_key = get_api_key("OpenAIApiKey")
            except (ClientError, KeyError) as e:
                logger.error("Failed to retrieve OpenAI API key: %s", str(e))
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
            agent = TextAgent(prompt_path, model_config, ModelType.OPENAI)
        elif agent_type == AgentType.CONTENT:
            agent = ContentAgent(prompt_path, model_config, ModelType.OPENAI)
        else:
            logger.error("Unsupported agent type: %s", agent_type)
            raise ValueError(f"Unsupported agent type: {agent_type}")

        logger.info("Successfully created OpenAI %s agent", agent_type.value)
        return agent

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
        logger.info(
            "Creating Gemini agent: model=%s, agent_type=%s",
            model_id.value,
            agent_type.value,
        )

        if api_key is None:
            try:
                api_key = get_api_key("GeminiApiKey")
            except (ClientError, KeyError) as e:
                logger.error("Failed to retrieve Gemini API key: %s", str(e))
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
            agent = TextAgent(prompt_path, model_config, ModelType.GEMINI)
        elif agent_type == AgentType.CONTENT:
            agent = ContentAgent(prompt_path, model_config, ModelType.GEMINI)
        else:
            logger.error("Unsupported agent type: %s", agent_type)
            raise ValueError(f"Unsupported agent type: {agent_type}")

        logger.info("Successfully created Gemini %s agent", agent_type.value)
        return agent

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
