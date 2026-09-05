"""Dataclasses for keeping track of the story state agent."""

from typing import Annotated

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from .models.content import Phrase, PhraseAnalysis
from .models.progress import Progress


def _candidates_reducer(existing: list[str], update: list[str] | None) -> list[str]:
    if update is None:
        return []
    return existing + update


def _inspector_results_reducer(
    existing: list[Phrase], update: list[Phrase] | None
) -> list[Phrase]:
    if update is None:
        return []
    return existing + update


class StoryState(TypedDict):
    """State of the story designer agent."""

    messages: Annotated[list[BaseMessage], add_messages]
    story_lines: list[str]
    narrator_candidates: Annotated[list[str], _candidates_reducer]
    inspector_results: Annotated[list[Phrase], _inspector_results_reducer]
    progress: Progress
    pending_analyses: PhraseAnalysis
    turn_count: int
    turn_summaries: dict[int, str]
    wind_down_turns: int
    wind_down: bool
    full_story: str
