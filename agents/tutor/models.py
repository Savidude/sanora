from typing import Literal
from enum import Enum
from pydantic import BaseModel


class LlmModel(str, Enum):
    """Enum for supported LLM models"""

    OPENAI_GPT_OSS_20B = "openai.gpt-oss-20b-1:0"
    AMAZON_NOVA_2_LITE = "eu.amazon.nova-2-lite-v1:0"
    ANTHROPIC_CLAUDE_HAIKU_4_5 = "eu.anthropic.claude-haiku-4-5-20251001-v1:0"


class TutorModel(BaseModel):
    """Model for the tutor agent"""

    model: LlmModel
    max_tokens: int = 256


class State(BaseModel):
    """Current state of the story"""

    event: str
    user_action: str


class StateEvaluatorOutput(BaseModel):
    """Output of the state evaluator"""

    user_decision_match: bool


class ForceDecisionOutput(BaseModel):
    """Output of the force-decision gate."""

    should_force: bool


class FallbackNudgeOutput(BaseModel):
    """Structured story text for a non-advancing fallback nudge."""

    acknowledgement: str
    barrier: str
    question: str


class FallbackForcedOutput(BaseModel):
    """Structured story text after a forced story decision."""

    acknowledgement: str
    continuation: str


class FallbackContext(BaseModel):
    """Context describing how the fallback facilitator should respond."""

    mode: Literal["nudge", "forced"]
    forced_action: str | None
