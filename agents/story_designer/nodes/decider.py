"""Decider node implementation for selecting the best candidate story line based on inspector
results and updating the story state.
"""

from ..state import StoryState
from ..models.content import Phrase
from ..models.progress import Progress
from ..characters import NARRATOR


def _get_identified_grammar_concepts(inspector_result: Phrase) -> list[str]:
    """Extract identified grammar concepts from an inspector result."""
    return [f.grammar_concept_code for f in inspector_result.analysis.grammar_findings]


def _score_phrase(inspector_result: Phrase, progress: Progress) -> int:
    """Score a phrase based on the number of newly identified grammar concepts."""

    newly_identified_concepts = 0

    identified_grammar_concept_codes = _get_identified_grammar_concepts(
        inspector_result
    )
    for code in identified_grammar_concept_codes:
        current_grammar_progess = progress.get_grammar_progress(code)
        if not current_grammar_progess.identified:
            newly_identified_concepts += 1

    return newly_identified_concepts


def decider(state: StoryState) -> dict:
    """Decider node to select the best candidate story line based on inspector results and update
    the story state."""
    inspector_results = state.get("inspector_results", [])
    if not inspector_results:
        raise ValueError("decider reached with no inspector_results in state")

    phrases_with_scores = [
        (phrase, _score_phrase(phrase, state["progress"]))
        for phrase in inspector_results
    ]

    # select the phrase with the most newly identified grammar concepts
    best_phrase = max(phrases_with_scores, key=lambda x: x[1])[0]
    story_line = f"{NARRATOR.name}: {best_phrase.content}"

    new_story_lines = list(state.get("story_lines", [])) + [story_line]

    return {
        "story_lines": new_story_lines,
        "narrator_candidates": None,
        "inspector_results": None,
        "pending_analyses": best_phrase.analysis,
    }
