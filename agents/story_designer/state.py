"""Dataclasses for keeping track of the story state agent."""

from typing import Annotated
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from .models.progress import Progress


def _candidates_reducer(existing: list[str], update: list[str] | None) -> list[str]:
    if update is None:
        return []
    return existing + update


class StoryState(TypedDict):
    """State of the story designer agent."""

    messages: Annotated[list[BaseMessage], add_messages]
    story_lines: list[str]
    narrator_candidates: Annotated[list[str], _candidates_reducer]
    progress: Progress
    wind_down: bool
