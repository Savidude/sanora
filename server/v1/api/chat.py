"""API resources for agent chat functionality."""

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError

from ..models.agent_comms import PromptRequest, AgentResponse, TutorResponseData

from ..service.agent_runtimes import AgentType, Runtime
from ..service.agent_communication import (
    AgentCommunicationService,
    agent_communication_service,
)
from ...exceptions import (
    UnexpectedAgentResponseError,
    InvalidRuntimeError,
    AgentInvocationError,
)

chat_router = APIRouter(prefix="/chat", tags=["chat"])


@chat_router.post("/message")
async def create_chat(
    request: PromptRequest,
    service: AgentCommunicationService = Depends(agent_communication_service),
) -> AgentResponse:
    """Send a message to the tutor agent

    Args:
        request: The prompt request containing message and session ID
        service: The agent communication service dependency

    Returns:
        AgentResponse: The response from the tutor agent

    Raises:
        HTTPException: If there is an error invoking the agent or processing the response
    """
    tutor_agent_runtime = Runtime(AgentType.TUTOR, "path/to/tutor/agent/runtime/arn")

    try:
        response = service.invoke_agent(
            agent_runtime=tutor_agent_runtime, request=request
        )
    except AgentInvocationError as e:
        return HTTPException(status_code=500, detail=str(e))

    try:
        agent_response = _generate_agent_response(
            agent_response=response,
            agent_runtime=tutor_agent_runtime,
            session_id=request.sessionId,
        )
        return agent_response
    except (InvalidRuntimeError, UnexpectedAgentResponseError) as e:
        return HTTPException(status_code=500, detail=str(e))


def _generate_agent_response(
    agent_response: dict, agent_runtime: Runtime, session_id: str
) -> AgentResponse:
    """Generate the AgentResponse based on the agent runtime type

    Args:
        agent_response: The raw response from the agent runtime
        agent_runtime: The agent runtime that was invoked
        session_id: The session ID used for the invocation

    Returns:
        AgentResponse: The structured response based on the agent runtime type

    Raises:
        InvalidRuntimeError: If the agent runtime type is unsupported
        UnexpectedAgentResponseError: If the agent response is malformed
    """

    response_body = agent_response["response"].read()
    response_data = json.loads(response_body)
    agent_response_str = response_data["content"][0]["text"]

    if agent_runtime.agent_type == AgentType.TUTOR:
        try:
            agent_response_json = json.loads(agent_response_str)
            response_data = TutorResponseData(**agent_response_json)
        except json.JSONDecodeError as e:
            raise UnexpectedAgentResponseError(
                "Failed to parse agent response JSON"
            ) from e
        except ValidationError as e:
            raise UnexpectedAgentResponseError(
                "Missing expected fields in agent response"
            ) from e

        return AgentResponse[TutorResponseData](
            success=True,
            data=response_data,
            session_id=session_id,
            timestamp=datetime.now(),
        )

    raise InvalidRuntimeError(
        f"Unsupported agent runtime type: {agent_runtime.agent_type}"
    )
