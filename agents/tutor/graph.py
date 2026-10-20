"""Defines the state graph for the tutor agent.
"""

from langgraph.graph import END, START, StateGraph

from .nodes.facilitator import fallback_facilitator, facilitator
from .nodes.force_decision_gate import force_decision_gate
from .nodes.orchestration import direct_message, initialise, route_from_start
from .nodes.state_evaluator import state_evaluator
from .state import TutorState

builder = StateGraph(TutorState)

builder.add_node("initialise", initialise)
builder.add_node("facilitator", facilitator)
builder.add_node("fallback_facilitator", fallback_facilitator)
builder.add_node("force_decision_gate", force_decision_gate)
builder.add_node("state_evaluator", state_evaluator)

builder.add_conditional_edges(
    START,
    route_from_start,
    ["initialise", "facilitator", "state_evaluator"],
)
builder.add_conditional_edges(
    "initialise",
    direct_message,
    ["facilitator", "state_evaluator"],
)

builder.add_edge("facilitator", END)
builder.add_edge("fallback_facilitator", END)

graph = builder.compile()
