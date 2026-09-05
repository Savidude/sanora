"""Defines the state graph for the story designer agent.
"""

from langgraph.graph import END, START, StateGraph

from .nodes.aggregator import aggregator
from .nodes.decider import decider
from .nodes.inspector import inspector, inspector_fan_out
from .nodes.narrator import narrator_fan_out, narrator_variation
from .nodes.orchestration import check_ending, initialise_story, wrap_story
from .nodes.protagonist import protagonist_turn
from .nodes.summarizer import summarizer
from .state import StoryState

builder = StateGraph(StoryState)

builder.add_node("initialise_story", initialise_story)
builder.add_node("narrator_variation", narrator_variation)
builder.add_node("inspector", inspector)
builder.add_node("decider", decider)
builder.add_node("aggregator", aggregator)
builder.add_node("protagonist_turn", protagonist_turn)
builder.add_node("summarizer", summarizer)
builder.add_node("wrap_story", wrap_story)

builder.add_edge(START, "initialise_story")
builder.add_conditional_edges(
    "initialise_story", narrator_fan_out, ["narrator_variation"]
)
builder.add_conditional_edges("narrator_variation", inspector_fan_out, ["inspector"])
builder.add_edge("inspector", "decider")
builder.add_edge("decider", "aggregator")
builder.add_edge("decider", "protagonist_turn")
builder.add_edge("aggregator", "summarizer")
builder.add_edge("protagonist_turn", "summarizer")
builder.add_edge("protagonist_turn", "summarizer")
builder.add_conditional_edges(
    "summarizer",
    check_ending,
    ["wrap_story", "narrator_variation"],
)
builder.add_edge("wrap_story", END)

graph = builder.compile()
