"""Contracts for the StoryDesigner AgentCore response."""

from pydantic import BaseModel, Field


class StoryTurnSummary(BaseModel):
    """Summary of one turn in the generated story."""

    event: str
    protagonist_decision: str


class GrammarConceptProgress(BaseModel):
    """Progress for one grammar concept in the generated story."""

    grammar_concept_code: str
    identified: bool = False
    total_findings: int = Field(default=0, ge=0)


class StoryDesignerResponse(BaseModel):
    """Response returned by the StoryDesigner AgentCore runtime."""

    scenario: str
    story_states: dict[int, StoryTurnSummary] = Field(default_factory=dict)
    grammar_progress: list[GrammarConceptProgress] = Field(default_factory=list)
