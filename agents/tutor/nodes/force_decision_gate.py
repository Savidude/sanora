"""Decide whether the tutor should force the current story decision."""

import json
from pathlib import Path

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import SystemMessage
from langgraph.types import Command

from ..models import FallbackContext, ForceDecisionOutput, LlmModel, TutorModel
from ..state import TutorState, story_state_to_dict

MODEL = TutorModel(model=LlmModel.ANTHROPIC_CLAUDE_HAIKU_4_5, max_tokens=256)


def _get_system_prompt(scenario: str) -> str:
    """Return the system prompt for the force-decision gate."""
    prompt_path = Path(__file__).parent.parent / "prompts" / "force_decision_gate.md"
    return prompt_path.read_text(encoding="utf-8").replace(
        "<STARTING_SCENARIO>", scenario
    )


def force_decision_gate(state: TutorState) -> Command:
    """Choose between nudging the user and forcing the current decision."""
    current_story_state = state.get("current_story_state", 1)
    story_state = story_state_to_dict(state["story_states"][current_story_state])
    fallback_attempts = state.get("fallback_attempts", 0)
    next_story_state = current_story_state + 1

    # Always give the user one clear nudge before considering a forced decision.
    should_force = False
    if fallback_attempts > 0 and next_story_state in state["story_states"]:
        llm = ChatBedrockConverse(
            model_id=MODEL.model,
            max_tokens=MODEL.max_tokens,
        ).with_structured_output(
            ForceDecisionOutput,
            method="json_schema",
        )

        messages = [SystemMessage(content=_get_system_prompt(state["scenario"]))]
        messages.extend(state.get("messages", []))
        messages.append(
            SystemMessage(
                content=json.dumps(
                    {
                        "event": story_state["event"],
                        "user_action": story_state["user_action"],
                        "fallback_attempts": fallback_attempts,
                    },
                    ensure_ascii=False,
                )
            )
        )

        decision = llm.invoke(messages)
        should_force = decision.should_force

    if should_force:
        update = {
            "current_story_state": next_story_state,
            "fallback_context": FallbackContext(
                mode="forced",
                forced_action=story_state["user_action"],
            ),
            "fallback_attempts": 0,
        }
    else:
        update = {
            "current_story_state": current_story_state,
            "fallback_context": FallbackContext(
                mode="nudge",
                forced_action=None,
            ),
            "fallback_attempts": fallback_attempts + 1,
        }

    return Command(update=update, goto="fallback_facilitator")
