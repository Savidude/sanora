"""Dataclasses for keeping track of the tutor state agent."""

import json
from pathlib import Path
from typing import Annotated

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from .models import State, FallbackContext

_STORY_STATES_PATH = Path(__file__).with_name("story_states.json")


StoryStateValue = State | dict[str, str]


def story_state_to_dict(story_state: StoryStateValue) -> dict[str, str]:
    """Return a story state as a normalized dictionary."""
    if isinstance(story_state, State):
        data = story_state.model_dump()
    else:
        data = dict(story_state)

    # Support story-state files created before the field was renamed.
    if "user_action" not in data and "protagonist_decision" in data:
        data["user_action"] = data["protagonist_decision"]

    return data


def load_story_states() -> dict[int, dict[str, str]]:
    """Return the turn summaries from story_states.json as story_states."""
    with _STORY_STATES_PATH.open(encoding="utf-8") as story_states_file:
        data = json.load(story_states_file)
    return {int(turn): state for turn, state in data["story_states"].items()}


def _assign_once(
    existing: dict[int, StoryStateValue] | None,
    update: dict[int, StoryStateValue] | None,
) -> dict[int, StoryStateValue]:
    """Keep the first non-empty story_states assignment for the session."""
    if existing:
        return existing
    return update or {}


class TutorState(TypedDict):
    """State of the tutor agent."""

    messages: Annotated[list[BaseMessage], add_messages]
    scenario: str
    story_states: Annotated[dict[int, StoryStateValue], _assign_once]
    current_story_state: int = 1
    fallback_context: FallbackContext | None
    fallback_attempts: int
