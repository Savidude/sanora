from langchain_aws import ChatBedrockConverse
from langchain_core.messages import SystemMessage, HumanMessage

from ..state import StoryState
from ..characters import NARRATOR, PROTAGONIST
from ..characters import LlmModel


def _extract_text(content) -> str:
    if isinstance(content, str):
        return content
    return "".join(
        block.get("text", "") if isinstance(block, dict) else str(block)
        for block in content
    )


def _build_story_so_far(story_lines: list[str], turn_summaries: dict[int, str]) -> str:

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
        history = "\n".join(f"Turn {k}: {v}" for k, v in sorted(turn_summaries.items()))
        previous_context = f"Story so far:\n{history}\n\n"

    content = f"{previous_context}Latest turn:\n{last_narrator}\n{last_protagonist}"
    return content


def summarizer(state: StoryState) -> dict:
    """Invoke the summarizer LLM to generate a concise summary of the latest turn in the story."""

    llm = ChatBedrockConverse(model_id=LlmModel.OPENAI_GPT_OSS_20B, max_tokens=256)

    story_lines = state.get("story_lines", [])
    current_story = state.get("turn_summaries") or {}

    response = llm.invoke(
        [
            SystemMessage(
                content=(
                    "You are a concise story summarizer. "
                    "You will be given a running history of previous turn summaries "
                    "and the latest narrator and protagonist exchange. "
                    "Write a plain summary of what happened in the latest turn in a maximum of 2 sentences."
                    "Do not include character names as labels."
                )
            ),
            HumanMessage(content=_build_story_so_far(story_lines, current_story)),
        ]
    )
    summary = _extract_text(response.content).strip()
    updated_summaries: dict = {
        "turn_summaries": {**current_story, state.get("turn_count", 0): summary},
    }
    if state.get("wind_down", False):
        updated_summaries["wind_down_turns"] = state.get("wind_down_turns", 0) + 1

    return updated_summaries
