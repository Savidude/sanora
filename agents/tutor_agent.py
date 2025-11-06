"""Resources for generating Tutor agents on AWS Agentocre"""

from dotenv import load_dotenv

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from models.base_agent import TextAgent, ContentAgent, BaseAgent
from models.agent_config import AgentConfig


load_dotenv()

app = BedrockAgentCoreApp()


def load_agents_from_config(config_path: str) -> dict[str, BaseAgent]:
    """Load agents from configuration file.

    Args:
        config_path (str): Path to the agent configuration file.

    Returns:
        dict: Dictionary of agent instances.
    """

    config = AgentConfig(config_path)
    tutors = config.create_all_agents()

    teacher: TextAgent = tutors["teacher_agent"]
    extractor: ContentAgent = tutors["extractor_agent"]
    return {
        "teacher": teacher,
        "extractor": extractor,
    }


tutor_agents = load_agents_from_config("agent_config.json")


@app.entrypoint
def invoke(payload):
    """Invoke the chat with agent function."""
    user_input = payload.get("prompt", "Hello! How can I help you today?")

    teacher = tutor_agents["teacher"]
    extractor = tutor_agents["extractor"]

    teacher_response = teacher.process(user_input)
    response_extraction = extractor.process(teacher_response)
    return response_extraction


if __name__ == "__main__":
    app.run()
