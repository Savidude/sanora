"""Builds the summarizer node that generates a concise summary of the latest turn in the story."""

import json
from common.logger import get_logger

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import SystemMessage, HumanMessage

from ..state import StoryState
from ..characters import NARRATOR, PROTAGONIST
from ..characters import LlmModel
from ..models.content import Summary
from .util import extract_text

logger = get_logger(__name__)


def _build_story_so_far(
    story_lines: list[str], turn_summaries: dict[int, Summary]
) -> str:

    # Find the last narrator and protagonist lines
    last_narrator = next(
        (
            line
            for line in reversed(story_lines)
            if line.startswith(f"{NARRATOR.name}:")
        ),
        None,
    )
    last_protagonist = next(
        (
            line
            for line in reversed(story_lines)
            if line.startswith(f"{PROTAGONIST.name}:")
        ),
        None,
    )

    previous_context = ""
    if turn_summaries:
        history_lines = []
        for turn, summary in sorted(turn_summaries.items()):
            history_lines.append(
                f"Turn {turn}:\n"
                f"Event: {summary.event}\n"
                f"Protagonist decision: {summary.protagonist_decision}"
            )
        if history_lines:
            history = "\n".join(history_lines)
            previous_context = f"Story so far:\n{history}\n\n"

    content = f"{previous_context}Latest turn:\n{last_narrator}\n{last_protagonist}"
    return content


def _parse_summary(response_content) -> Summary:
    """Parse a Summary from JSON, tolerating text before or after the JSON object."""
    text = extract_text(response_content).strip()
    start = text.find("{")
    if start == -1:
        raise ValueError("response did not contain a JSON object")

    parsed, _ = json.JSONDecoder().raw_decode(text[start:])
    return Summary.model_validate(parsed)


def summarizer(state: StoryState) -> dict:
    """Invoke the summarizer LLM to generate a concise summary of the latest turn in the story."""

    llm = ChatBedrockConverse(
        model_id=LlmModel.ANTHROPIC_CLAUDE_HAIKU_4_5, max_tokens=1048
    ).with_structured_output(
        Summary,
        method="json_schema",
    )

    story_lines = state.get("story_lines", [])
    current_story = state.get("turn_summaries") or {}

    messages = [
        SystemMessage(
            content=(
                "You are a concise story summarizer. "
                "You will be given a running history of previous turn summaries "
                "and the latest narrator and protagonist exchange. "
                "Return only a valid JSON object with exactly these string fields: "
                '"event" and "protagonist_decision". '
                "Do not use Markdown, code fences, prefixes, or any text outside "
                "the JSON object. Summarize the event described by the narrator in "
                "event, and the decision made by the protagonist in "
                "protagonist_decision. Keep each field concise and use no more "
                "than 2 sentences per field."
            )
        ),
        HumanMessage(content=_build_story_so_far(story_lines, current_story)),
    ]

    summary = None
    for attempt in range(3):
        raw_response = llm.invoke(messages)
        try:
            summary = _parse_summary(raw_response.content)
            break
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            logger.warning(
                "Summarizer returned invalid JSON",
                extra={"attempt": attempt + 1, "error": str(error)},
            )

    if summary is None:
        raise RuntimeError(
            "Summarizer failed to return a valid Summary after 3 attempts"
        )

    updated_turn_summaries = dict[int, Summary](current_story)
    updated_turn_summaries[state.get("turn_count", 0)] = summary

    updated_summaries: dict = {"turn_summaries": updated_turn_summaries}
    if state.get("wind_down", False):
        updated_summaries["wind_down_turns"] = state.get("wind_down_turns", 0) + 1

    return updated_summaries
