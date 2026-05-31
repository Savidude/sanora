"""Defines the state graph for the story designer agent.
"""

from langgraph.graph import END, START, StateGraph

from .state import StoryState
from .nodes.orchestration import initialise_story
from .nodes.narrator import narrator_fan_out, narrator_variation
from .nodes.inspector import inspector_fan_out, inspector

builder = StateGraph(StoryState)

builder.add_node("initialise_story", initialise_story)
builder.add_node("narrator_variation", narrator_variation)
builder.add_node("inspector", inspector)

builder.add_edge(START, "initialise_story")
builder.add_conditional_edges(
    "initialise_story", narrator_fan_out, ["narrator_variation"]
)
builder.add_conditional_edges("narrator_variation", inspector_fan_out, ["inspector"])
builder.add_edge("inspector", END)

graph = builder.compile()
