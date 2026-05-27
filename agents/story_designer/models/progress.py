"""Models for tracking progress in a story design session, including identified g
rammar concepts and word categories.
"""

from pydantic import BaseModel, Field


class GrammarConceptProgress(BaseModel):
    """Progress tracking for a specific grammar concept."""

    grammar_concept_code: str
    identified: bool = False
    total_findings: int = Field(default=0, ge=0)


class WordCategoryProgress(BaseModel):
    """Progress tracking for a specific word category."""

    word_category_code: str
    total_occurrences: int = Field(default=0, ge=0)


class Progress(BaseModel):
    """Progress of a story design session, tracking identified grammar concepts
    and word categories.
    """

    grammar_concept_progress: list[GrammarConceptProgress] = []
    word_category_progress: list[WordCategoryProgress] = []
