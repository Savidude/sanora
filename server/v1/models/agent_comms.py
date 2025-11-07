"""Communication models for request-response based communication with agentic systems"""

from datetime import datetime
from typing import Optional, List, TypeVar, Generic
from enum import Enum
from pydantic import BaseModel


class PromptRequest(BaseModel):
    """Required data for Agentcore invokation

    Attributes:
        message: The prompt message to send to the agent
        sessionId: The unique session identifier for tracking the conversation
    """

    message: str
    sessionId: str


class MessageType(str, Enum):
    """Message types for categorizing communication

    Attributes:
        INITIATION: Initial messages to start a conversation
        FEEDBACK: Messages providing feedback during the conversation
        CONCLUSION: Closing messages to end the conversation
    """

    INITIATION = "initiation"
    FEEDBACK = "feedback"
    CONCLUSION = "conclusion"


class ErrorType(str, Enum):
    """Error types for categorizing errors in communication

    Attributes:
        YES: Significant errors affecting understanding
        NO: No errors present
        MINOR: Minor errors not significantly affecting understanding
    """

    YES = "YES"
    NO = "NO"
    MINOR = "MINOR"


class ErrorDetail(BaseModel):
    """Details about user mistakes and corrections

    Atributes:
        user_mistake: The specific mistake made by the user
        corrections: List of suggested corrections for the mistake
        explanation: Explanation of the mistake and corrections
    """

    user_mistake: Optional[str] = None
    corrections: List[str] = []
    explanation: Optional[str] = None


class WordTip(BaseModel):
    """Tips for difficult words in the communication

    Attributes:
        finnish: The difficult word in Finnish
        english: The English translation of the difficult word
    """

    finnish: str
    english: str


class AgentResponseData(BaseModel):
    """Data returned from Agentcore invokation"""


ResponseDataType = TypeVar("ResponseDataType", bound=AgentResponseData)


class TutorResponseData(AgentResponseData):
    """Data returned from the invokation of the tutor agent

    Attributes:
        message_type: The type of message (initiation, feedback, conclusion)
        has_error: Indicates if there was an error in the user's response
        feedback_text: Feedback provided by the tutor agent
        error_details: Details about any mistakes made by the user
        greeting: Optional greeting message from the tutor agent
        scenario: Optional scenario description for context
        conversation_continuation: Text to continue the conversation
        word_tips: List of tips for difficult words encountered
    """

    message_type: MessageType
    has_error: ErrorType
    feedback_text: Optional[str] = None
    error_details: Optional[ErrorDetail] = None
    greeting: Optional[str] = None
    scenario: Optional[str] = None
    conversation_continuation: str
    word_tips: List[WordTip]


class AgentResponse(BaseModel, Generic[ResponseDataType]):
    """Response model for Agentcore invokation

    Attributes:
        success: Indicates if the invocation was successful
        data: The response data specific to the agent type
        session_id: The session ID used for the invocation
        timestamp: The timestamp of the response
    """

    success: bool = True
    data: TutorResponseData
    session_id: str
    timestamp: datetime
