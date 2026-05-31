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

    def get_unidentified_grammar_concepts(self) -> list[GrammarConceptProgress]:
        """Filter grammar concepts that haven't been identified yet."""
        return [gc for gc in self.grammar_concept_progress if not gc.identified]

    def get_least_identified_word_categories(self) -> list[WordCategoryProgress]:
        """Get the 10 least identified word categories sorted by occurrence."""
        return sorted(self.word_category_progress, key=lambda wc: wc.total_occurrences)[
            :10
        ]
