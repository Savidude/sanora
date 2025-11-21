"""Collection of AI agents that have been deployed"""

from enum import Enum

import boto3


class AgentType(str, Enum):
    """Types of agents available in the system"""

    TUTOR = "tutor"


class Runtime:
    """Base class for all agents."""

    def __init__(self, agent_type: AgentType, runtime_arn: str):
        """Define the attributes required to reference Agent Runrimes

        Args:
            arn_path: SSM path that consists of the ARN of the agent runtime
        """

        self.ssm_client = boto3.client("ssm", region_name="eu-central-1")
        self.agent_type = agent_type
        self.runtime_arn = runtime_arn
