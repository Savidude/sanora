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

    def get_grammar_progress(self, grammar_concept_code: str) -> GrammarConceptProgress:
        """Get the progress for a specific grammar concept code."""
        for progress in self.grammar_concept_progress:
            if progress.grammar_concept_code == grammar_concept_code:
                return progress
        raise ValueError(f"Grammar concept code '{grammar_concept_code}' not found")

    def update_grammar_concept_progress(
        self, grammar_concept_code: str, count: int = 1
    ) -> None:
        """Update the progress for a specific grammar concept code."""
        for progress in self.grammar_concept_progress:
            if progress.grammar_concept_code == grammar_concept_code:
                progress.total_findings += count
                progress.identified = True
                return
        raise ValueError(f"Grammar concept code '{grammar_concept_code}' not found")

    def update_word_category_progress(
        self, word_category_code: str, count: int = 1
    ) -> None:
        """Update the progress for a specific word category code."""
        for progress in self.word_category_progress:
            if progress.word_category_code == word_category_code:
                progress.total_occurrences += count
                return
        raise ValueError(f"Word category code '{word_category_code}' not found")
