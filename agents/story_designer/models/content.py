"""Models represnenting the identified grammar concepts and word categories in 
phrases of a story.
"""

from pydantic import BaseModel


class GrammarFinding(BaseModel):
    """Identified grammar concepts in a given phrase."""

    grammar_concept_code: str
    matched_text: str


class WordFinding(BaseModel):
    """Identified word categories in a given phrase."""

    word_category_code: str
    matched_text: str


class PhraseAnalysis(BaseModel):
    """Analysis of a phrase, including identified grammar concepts and word categories."""

    grammar_findings: list[GrammarFinding] = []
    word_findings: list[WordFinding] = []


class Phrase(BaseModel):
    """A phrase in the story, along with its analysis of identified grammar concepts
    and word categories.
    """

    content: str
    analysis: PhraseAnalysis
