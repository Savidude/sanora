"""Service layer for the agent communication."""

import logging
import json


import boto3

from ...exceptions import AgentInvocationError

from ..models.agent_comms import PromptRequest
from .agent_runtimes import Runtime

logger = logging.getLogger(__name__)


class AgentCommunicationService:
    """Service class for handling agent communication logic."""

    def __init__(self):
        self.agentcore_client = boto3.client(
            "bedrock-agentcore", region_name="eu-central-1"
        )

    def invoke_agent(self, agent_runtime: Runtime, request: PromptRequest) -> dict:
        """Invoke the specified agent runtime with the given prompt request

        Args:
            agent_runtime: The agent runtime to invoke
            request: The prompt request containing message and session ID
        Returns:
            AgentResponse: The response from the agent runtime

        Raises:
            AgentInvocationError: If there is an error invoking the agent runtime
        """

        payload = json.dumps({"prompt": request.message})
        session_id = f"session_{request.sessionId}"

        logger.info(
            "Invoking agent runtime %s with session ID %s",
            agent_runtime.agent_type,
            session_id,
        )
        try:
            response = self.agentcore_client.invoke_agent_runtime(
                agentRuntimeArn=agent_runtime.get_runtime_arn(),
                runtimeSessionId=session_id,
                payload=payload,
                qualifier="DEFAULT",  # Optional
            )

            logger.info(
                "Received response from agent runtime %s for session ID %s",
                agent_runtime.agent_type,
                session_id,
            )
            return response
        except Exception as e:
            raise AgentInvocationError(
                f"Failed to invoke agent runtime {agent_runtime.agent_type}"
            ) from e


def agent_communication_service() -> AgentCommunicationService:
    """Dependency injector for AgentCommunicationService"""
    return AgentCommunicationService()
