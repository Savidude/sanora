"""Contains nodes responsible for orchestrating the agents in the Story Designer."""

import os
from langchain_core.messages import SystemMessage

from ..models.curriculum import Curriculum
from ..models.progress import GrammarConceptProgress, Progress, WordCategoryProgress
from ..state import StoryState
from .narrator import narrator_fan_out

CURRICULUM: Curriculum = Curriculum.load()


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
    opening = state["story_opening"].strip()
    story_opening = SystemMessage(content=opening)
    return {
        "messages": [story_opening],
        "story_lines": [f"--- {opening} ---"],
        "progress": _initialize_progress(),
        "wind_down": False,
    }


def check_ending(state: StoryState) -> dict:
    """Check if the story should be wrapped up based on the wind down flag and turn count,
    and either trigger the wrap up or fan out to the narrator for the next iteration.
    """
    if state.get("wind_down", False) and state.get("wind_down_turns", 0) >= int(
        os.getenv("WIND_DOWN_TURN_LIMIT")
    ):
        return "wrap_story"

    return narrator_fan_out(state)


def wrap_story(state: StoryState) -> dict:
    """Wrap up the story by compiling the full story text from the story lines."""
    lines = state.get("story_lines", [])
    formatted = "\n\n".join(lines)
    return {"full_story": formatted}
