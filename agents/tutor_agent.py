"""Resources for generating Tutor agents on AWS Agentocre"""

import logging
from dotenv import load_dotenv

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from models.base_agent import TextAgent, ContentAgent, BaseAgent
from models.agent_config import AgentConfig


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

app = BedrockAgentCoreApp()


def load_agents_from_config(config_path: str) -> dict[str, BaseAgent]:
    """Load agents from configuration file.

    Args:
        config_path (str): Path to the agent configuration file.

    Returns:
        dict: Dictionary of agent instances.
    """
    logger.info("Loading agents from config: %s", config_path)

    try:
        config = AgentConfig(config_path)
        tutors = config.create_all_agents()

        teacher: TextAgent = tutors["teacher_agent"]
        extractor: ContentAgent = tutors["extractor_agent"]

        logger.info("Successfully loaded teacher and extractor agents")
        return {
            "teacher": teacher,
            "extractor": extractor,
        }
    except Exception as e:
        logger.error("Failed to load agents from config: %s", str(e), exc_info=True)
        raise


tutor_agents = load_agents_from_config("agent_config.json")


@app.entrypoint
def invoke(payload):
    """Invoke the chat with agent function."""
    user_input = payload.get("prompt", "")
    logger.info("Received invoke request with input length: %d", len(user_input))

    try:
        teacher = tutor_agents["teacher"]
        extractor = tutor_agents["extractor"]

        logger.debug("Processing input with teacher agent: %s...", user_input[:100])
        teacher_response = teacher.process(user_input)
        logger.info("Teacher agent processing complete")

        logger.debug("Processing teacher response with extractor agent")
        response_extraction = extractor.process(teacher_response)
        logger.info("Extractor agent processing complete")

        return response_extraction
    except Exception as e:
        logger.error("Error during invoke: %s", str(e), exc_info=True)
        raise


if __name__ == "__main__":
    app.run()
