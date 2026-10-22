from typing import Literal
from enum import Enum, StrEnum
from pydantic import BaseModel, Field, field_validator, model_validator


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


class ResponseResult(StrEnum):
    """Result of the response"""

    CORRECT = "correct"
    MINOR = "minor"
    INCORRECT = "incorrect"


class Expression(BaseModel):
    """Word or phrase given to the user in Finnish and English"""

    finnish: str = Field(min_length=1)
    english: str = Field(min_length=1)

    @field_validator("finnish", "english")
    @classmethod
    def validate_text(cls, value: str) -> str:
        """Reject empty or whitespace-only correction values."""
        value = value.strip()
        if not value:
            raise ValueError("correction text must not be blank")
        return value


class ErrorDetails(BaseModel):
    """Details of the error"""

    user_mistake: str = Field(min_length=1)
    corrections: list[Expression] = Field(min_length=1)
    explanation: str = Field(min_length=1)

    @field_validator("user_mistake", "explanation")
    @classmethod
    def validate_text(cls, value: str) -> str:
        """Reject empty or whitespace-only error details."""
        value = value.strip()
        if not value:
            raise ValueError("error detail text must not be blank")
        return value


class Review(BaseModel):
    """Review of the user response"""

    result: ResponseResult
    translation_en: str | None
    feedback: str | None = Field(min_length=1)
    error_details: ErrorDetails | None

    @model_validator(mode="after")
    def validate_result_consistency(self):
        """Require fields that correspond to the selected review result."""
        if self.feedback is None or not self.feedback.strip():
            raise ValueError("feedback must not be blank")

        if self.result == ResponseResult.CORRECT:
            if self.translation_en is None or not self.translation_en.strip():
                raise ValueError("correct reviews require a non-blank translation_en")
            if self.error_details is not None:
                raise ValueError("correct reviews cannot contain error_details")
            return self

        if self.translation_en is not None:
            raise ValueError(
                "minor and incorrect reviews cannot contain translation_en"
            )
        if self.error_details is None:
            raise ValueError("minor and incorrect reviews require error_details")
        return self


class Translation(BaseModel):
    """Output of the translator"""

    translation: str
    hints: list[Expression] = Field(min_length=3, max_length=5)

    @field_validator("hints")
    @classmethod
    def validate_hints(cls, value: list[Expression]) -> list[Expression]:
        """Require each Finnish hint to contain exactly one word."""
        if any(len(hint.finnish.split()) != 1 for hint in value):
            raise ValueError("each Finnish hint must contain exactly one word")
        return value
