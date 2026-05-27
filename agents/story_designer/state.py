"""Dataclasses for keeping track of the story state agent."""

from typing import Annotated
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from models.progress import Progress


class StoryState(TypedDict):
    """State of the story designer agent."""

    messages: Annotated[list[BaseMessage], add_messages]
    progress: Progress
