"""State evaluator function for the tutor agent."""

import json
from pathlib import Path

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import SystemMessage
from langgraph.graph import END
from langgraph.types import Command

from ..models import LlmModel, StateEvaluatorOutput, TutorModel
from ..state import TutorState, story_state_to_dict

MODEL = TutorModel(model=LlmModel.ANTHROPIC_CLAUDE_HAIKU_4_5, max_tokens=512)


def _get_system_prompt_for_state_evaluator(scenario: str) -> str:
    """Return the system prompt for the state evaluator."""
    prompt_path = Path(__file__).parent.parent / "prompts" / "state_evaluator.md"
    return prompt_path.read_text(encoding="utf-8").replace(
        "<STARTING_SCENARIO>", scenario
    )


def state_evaluator(state: TutorState) -> Command:
    """Evaluate whether the user's latest response matches the current decision."""
    current_story_state = state.get("current_story_state", 1)
    story_state = story_state_to_dict(state["story_states"][current_story_state])

    llm = (
        ChatBedrockConverse(model_id=MODEL.model, max_tokens=MODEL.max_tokens)
        .with_structured_output(
            StateEvaluatorOutput,
            method="function_calling",
        )
        .with_retry(stop_after_attempt=3)
    )

    messages = [
        SystemMessage(content=_get_system_prompt_for_state_evaluator(state["scenario"]))
    ]
    messages.extend(state.get("messages", []))
    messages.append(SystemMessage(content=json.dumps(story_state, ensure_ascii=False)))

    evaluation = llm.invoke(messages)
    user_decision_match = evaluation.user_decision_match
    next_story_state = current_story_state + int(user_decision_match)
    update = {"current_story_state": next_story_state}

    if not user_decision_match:
        return Command(update=update, goto="force_decision_gate")

    update["fallback_context"] = None
    update["fallback_attempts"] = 0
    if next_story_state in state["story_states"]:
        return Command(update=update, goto="facilitator")
    return Command[str](update=update, goto=END)
