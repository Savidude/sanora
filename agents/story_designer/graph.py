"""Defines the state graph for the story designer agent.
"""

from langgraph.graph import END, START, StateGraph

from state import StoryState
from nodes.orchestration import initialise_story

builder = StateGraph(StoryState)

builder.add_node("initialise_story", initialise_story)

builder.add_edge(START, "initialise_story")
builder.add_edge("initialise_story", END)

graph = builder.compile()
