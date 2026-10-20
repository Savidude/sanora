"""Facilitator function for the tutor agent."""

import json
from pathlib import Path

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ..state import TutorState, story_state_to_dict
from ..models import (
    FallbackContext,
    FallbackForcedOutput,
    FallbackNudgeOutput,
    LlmModel,
    TutorModel,
)

FACILITATOR_MODEL = TutorModel(
    model=LlmModel.ANTHROPIC_CLAUDE_HAIKU_4_5, max_tokens=256
)
FALLBACK_FACILITATOR_MODEL = TutorModel(
    model=LlmModel.ANTHROPIC_CLAUDE_HAIKU_4_5, max_tokens=512
)


def _get_system_prompt_for_facilitator(scenario: str) -> str:
    """Return the system prompt for the facilitator."""
    facilitator_prompt_path = (
        Path(__file__).parent.parent / "prompts" / "facilitator_prompt.md"
    )
    return facilitator_prompt_path.read_text(encoding="utf-8").replace(
        "<STARTING_SCENARIO>", scenario
    )


def _get_system_prompt_for_nudge(scenario: str) -> str:
    """Return the system prompt for a non-advancing fallback nudge."""
    nudge_prompt_path = (
        Path(__file__).parent.parent / "prompts" / "nudge_facilitator.md"
    )
    return nudge_prompt_path.read_text(encoding="utf-8").replace(
        "<STARTING_SCENARIO>", scenario
    )


def _get_system_prompt_for_forced_facilitator(scenario: str) -> str:
    """Return the system prompt for a forced story continuation."""
    forced_prompt_path = (
        Path(__file__).parent.parent / "prompts" / "forced_facilitator.md"
    )
    return forced_prompt_path.read_text(encoding="utf-8").replace(
        "<STARTING_SCENARIO>", scenario
    )


def _get_latest_user_message(state: TutorState) -> HumanMessage | None:
    """Return only the latest user message from the conversation."""
    return next(
        (
            message
            for message in reversed(state.get("messages", []))
            if isinstance(message, HumanMessage)
        ),
        None,
    )


def _get_story_history(
    state: TutorState, current_story_state: int
) -> list[dict[str, str]]:
    """Return trusted events and decisions from the story's previous states."""
    history = []
    for story_state_number in sorted(state["story_states"]):
        if story_state_number >= current_story_state:
            continue

        previous_story_state = story_state_to_dict(
            state["story_states"][story_state_number]
        )
        history.append(
            {
                "state": str(story_state_number),
                "event": previous_story_state["event"],
                "user_action": previous_story_state["user_action"],
            }
        )
    return history


def facilitator(state: TutorState) -> dict:
    """Facilitate the tutor's turn"""
    llm = ChatBedrockConverse(
        model_id=FACILITATOR_MODEL.model, max_tokens=FACILITATOR_MODEL.max_tokens
    )

    current_story_state = state["current_story_state"]
    story_state = story_state_to_dict(
        state["story_states"][current_story_state]
    )
    story_history = _get_story_history(state, current_story_state)
    messages = [
        SystemMessage(content=_get_system_prompt_for_facilitator(state["scenario"])),
    ]
    if story_history:
        messages.append(
            SystemMessage(
                content=(
                    "TRUSTED STORY HISTORY (earlier states, in order):\n"
                    f"{json.dumps(story_history, ensure_ascii=False)}"
                )
            )
        )
    messages.append(
        SystemMessage(
            content=(
                "AUTHORITATIVE CURRENT STORY CONTEXT:\n"
                f"{json.dumps(
                    {
                        'event': story_state['event'],
                        'expected_user_action': story_state['user_action'],
                    },
                    ensure_ascii=False,
                )}"
            )
        )
    )
    messages.append(
        SystemMessage(
            content=(
                "TURN BOUNDARY: Narrate the current event before the "
                "expected_user_action. Do not perform that action, continue "
                "past it, or invent its consequences. Ask the user to choose "
                "the expected_user_action."
            )
        )
    )

    response = llm.invoke(messages)
    return {
        "messages": [AIMessage(content=response.content)],
    }


def _nudge_fallback_facilitator(state: TutorState, story_state: dict[str, str]) -> dict:
    """Generate a non-advancing nudge for the user's response."""
    llm = ChatBedrockConverse(
        model_id=FALLBACK_FACILITATOR_MODEL.model,
        max_tokens=FALLBACK_FACILITATOR_MODEL.max_tokens,
    ).with_structured_output(
        FallbackNudgeOutput,
        method="json_schema",
    )
    latest_user_message = _get_latest_user_message(state)
    messages = [
        SystemMessage(content=_get_system_prompt_for_nudge(state["scenario"])),
        SystemMessage(
            content=json.dumps(
                {
                    "event": story_state["event"],
                    "user_action": story_state["user_action"],
                },
                ensure_ascii=False,
            )
        ),
    ]
    if latest_user_message is not None:
        messages.append(latest_user_message)
    messages.append(
        HumanMessage(
            content=(
                "Write the structured nudge now. Keep the acknowledgement "
                "neutral, come up with one creative temporary barrier on your "
                "own, and use it to make the trusted user_action feel like a "
                "natural next step."
            )
        )
    )
    response = llm.invoke(messages)
    acknowledgement = response.acknowledgement.strip()
    barrier = response.barrier.strip()
    question = response.question.strip()
    if acknowledgement and acknowledgement[-1] not in ".!?":
        acknowledgement += "."
    if barrier and barrier[-1] not in ".!?":
        barrier += "."
    if question and not question.endswith("?"):
        question += "?"
    return {
        "messages": [
            AIMessage(
                content=f"{acknowledgement} {barrier} {question}".strip()
            )
        ],
        "fallback_context": None,
    }


def _forced_fallback_facilitator(
    state: TutorState,
    story_state: dict[str, str],
    fallback_context: FallbackContext,
) -> dict:
    """Generate a creative continuation after the trusted action was forced."""
    llm = ChatBedrockConverse(
        model_id=FALLBACK_FACILITATOR_MODEL.model,
        max_tokens=FALLBACK_FACILITATOR_MODEL.max_tokens,
    ).with_structured_output(
        FallbackForcedOutput,
        method="json_schema",
    )
    latest_user_message = _get_latest_user_message(state)
    latest_user_choice = (
        latest_user_message.content if latest_user_message is not None else ""
    )
    messages = [
        SystemMessage(
            content=_get_system_prompt_for_forced_facilitator(state["scenario"])
        )
    ]
    messages.append(
        SystemMessage(
            content=json.dumps(
                {
                    **story_state,
                    "user_choice": latest_user_choice,
                    "fallback_mode": fallback_context.mode,
                    "forced_action": fallback_context.forced_action,
                },
                ensure_ascii=False,
            )
        )
    )
    messages.append(HumanMessage(content="Write the forced continuation now."))

    response = llm.invoke(messages)
    acknowledgement = response.acknowledgement.strip()
    continuation = response.continuation.strip()
    if acknowledgement and acknowledgement[-1] not in ".!?":
        acknowledgement += "."
    if continuation and "?" not in continuation:
        continuation = continuation.rstrip(".!?") + "?"
    return {
        "messages": [AIMessage(content=f"{acknowledgement} {continuation}".strip())],
        "fallback_context": None,
    }


def fallback_facilitator(state: TutorState) -> dict:
    """Route fallback generation to the active fallback mode."""
    current_story_state = state.get("current_story_state", 1)
    story_state = story_state_to_dict(state["story_states"][current_story_state])
    fallback_context = state.get("fallback_context") or FallbackContext(
        mode="nudge",
        forced_action=None,
    )

    if fallback_context.mode == "nudge":
        return _nudge_fallback_facilitator(state, story_state)
    return _forced_fallback_facilitator(state, story_state, fallback_context)
