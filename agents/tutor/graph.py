"""Defines the state graph for the tutor agent.
"""

from langgraph.graph import END, START, StateGraph

from .nodes.facilitator import fallback_facilitator, facilitator
from .nodes.force_decision_gate import force_decision_gate
from .nodes.orchestration import direct_message, initialise, route_from_start
from .nodes.state_evaluator import state_evaluator
from .nodes.language import reviewer, translator
from .state import TutorState

builder = StateGraph(TutorState)

builder.add_node("initialise", initialise)
builder.add_node("reviewer", reviewer)
builder.add_node("facilitator", facilitator)
builder.add_node("translator", translator)
builder.add_node("fallback_facilitator", fallback_facilitator)
builder.add_node("force_decision_gate", force_decision_gate)
builder.add_node("state_evaluator", state_evaluator)

builder.add_conditional_edges(
    START,
    route_from_start,
    ["initialise", "facilitator", "reviewer"],
)
builder.add_conditional_edges(
    "initialise",
    direct_message,
    ["facilitator", "reviewer"],
)

builder.add_edge("reviewer", "state_evaluator")
builder.add_edge("facilitator", "translator")
builder.add_edge("fallback_facilitator", "translator")
builder.add_edge("translator", END)

graph = builder.compile()
