"""Collection of AI agents that have been deployed"""

from enum import Enum

import boto3


class AgentType(str, Enum):
    """Types of agents available in the system"""

    TUTOR = "tutor"


class Runtime:
    """Base class for all agents."""

    def __init__(self, agent_type: AgentType, arn_path: str):
        """Define the attributes required to reference Agent Runrimes

        Args:
            arn_path: SSM path that consists of the ARN of the agent runtime
        """

        self.ssm_client = boto3.client("ssm", region_name="eu-central-1")
        self.agent_type = agent_type
        self.arn_path = arn_path

    def get_runtime_arn(self) -> str:
        """Get the runtime ARN for the agent from SSM"""

        # TODO: Uncomment when SSM is set up
        # agent_arn = self.ssm_client.get_parameter(Name=self.arn_path)["Parameter"][
        #     "Value"
        # ]
        agent_arn = "arn:aws:bedrock-agentcore:eu-central-1:442042519937:runtime/tutor_agent-B7GpkJ8mDO"
        return agent_arn
