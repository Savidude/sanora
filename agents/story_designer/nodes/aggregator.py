"""Implementation of the aggregator node for the story designer"""

from ..state import StoryState
from ..models.progress import Progress


def aggregator(state: StoryState) -> dict:
    """Aggregator node to process inspector results, update progress on grammar concepts and word
    categories, and prepare for the next iteration of story line generation.
    """

    analysis = state["pending_analyses"]
    progress: Progress = state["progress"]

    grammar_counts: dict[str, int] = {}
    for gf in analysis.grammar_findings:
        grammar_counts[gf.grammar_concept_code] = (
            grammar_counts.get(gf.grammar_concept_code, 0) + 1
        )

    word_counts: dict[str, int] = {}
    for wf in analysis.word_findings:
        word_counts[wf.word_category_code] = (
            word_counts.get(wf.word_category_code, 0) + 1
        )

    for grammar_concept_code, count in grammar_counts.items():
        progress.update_grammar_concept_progress(grammar_concept_code, count)

    for word_category_code, count in word_counts.items():
        progress.update_word_category_progress(word_category_code, count)
