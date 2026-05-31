"""Contains nodes responsible for orchestrating the agents in the Story Designer."""

from langchain_core.messages import SystemMessage

from ..state import StoryState
from ..models.curriculum import Curriculum
from ..models.progress import Progress, GrammarConceptProgress, WordCategoryProgress

CURRICULUM: Curriculum = Curriculum.load()

STORY_OPENING = """SCENE: A hotel lobby, the morning of a life-changing job interview.

Pip has just opened their suitcase in the room and found the wrong one — inside:
a book of poetry, one red high-heeled shoe, and a photo of his childhood home.
A folded note rests on top, telling Pip to meet someone at a local café.

The story begins now.
"""


def _initialize_progress() -> Progress:
    """Initialise the progress tracking for a story design session, based on the curriculum."""

    grammar_concept_progress = [
        GrammarConceptProgress(grammar_concept_code=gc.code)
        for level in CURRICULUM.levels
        for gc in level.grammar_concepts
    ]
    word_category_progress = [
        WordCategoryProgress(word_category_code=wc.code)
        for level in CURRICULUM.levels
        for wc in level.word_categories
    ]
    return Progress(
        grammar_concept_progress=grammar_concept_progress,
        word_category_progress=word_category_progress,
    )


def initialise_story(state: StoryState) -> dict:  # pylint: disable=unused-argument
    """Initialise the story state."""
    story_opening = SystemMessage(content=STORY_OPENING)
    return {
        "messages": [story_opening],
        "story_lines": [f"--- {STORY_OPENING.strip()} ---"],
        "progress": _initialize_progress(),
        "wind_down": False,
    }
