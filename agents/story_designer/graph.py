"""Defines the state graph for the story designer agent.
"""

from langgraph.graph import END, START, StateGraph

from .state import StoryState
from .nodes.orchestration import initialise_story
from .nodes.narrator import narrator_fan_out, narrator_variation

builder = StateGraph(StoryState)

builder.add_node("initialise_story", initialise_story)
builder.add_node("narrator_fan_out", narrator_fan_out)
builder.add_node("narrator_variation", narrator_variation)

builder.add_edge(START, "initialise_story")
builder.add_conditional_edges(
    "initialise_story", narrator_fan_out, ["narrator_variation"]
)
builder.add_edge("narrator_variation", END)

graph = builder.compile()
