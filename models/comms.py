"""Communication models for request-response based communication with agentic systems"""

from typing import Dict, Any
from pydantic import BaseModel


class PromptRequest(BaseModel):
    """Required data for Agentcore invokation"""

    message: str
    sessionId: str


class ResponseData(BaseModel):
    """Data returned from Agentcore invokation"""

    agentResponse: Dict[Any, Any]


# Pydantic model for response
class AgentResponse(BaseModel):
    """Response model for Agentcore invokation"""

    success: bool = True
    data: ResponseData
    session_id: str
