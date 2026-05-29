"""Contains nodes required for the functioning of the narrator agent"""

from langchain_aws import ChatBedrockConverse
from langgraph.types import Send

from ..characters import Character, LlmModel, build_messages_for_character
from ..state import StoryState
from .protagonist import PROTAGONIST

NARRATOR = Character(
    name="Narrator",
    model=LlmModel.OPENAI_GPT_OSS_20B,
    max_tokens=256,
    system_prompt=(
        """You are the Narrator of a short story for adults learning English.
        
        YOUR ROLE:
        - Say only the most important thing happening right now.
        - Use short, simple sentences.
        - Use common, everyday words that average adults use in daily life.
        - Use very little description.
        - Give voice to simple side characters when needed, such as a guard, a stranger, etc.
        - ALWAYS end your final sentence with a direct nudge for the user — a short question or a clear cue (e.g. "Will you go in?"). Never end a turn without this nudge.
        - Write no more than 3 sentences per turn.
        - Prefer 1 or 2 short sentences unless 3 are really needed.
        """
    ),
)


def _extract_text(content) -> str:
    if isinstance(content, str):
        return content
    return "".join(
        block.get("text", "") if isinstance(block, dict) else str(block)
        for block in content
    )


def narrator_variation(state: StoryState) -> dict:
    """Build the history of the story for the narrator's turn, invoke the narrator's LLM to
    generate a new story line, and return it as a candidate for the next story line.
    """
    temperature = state.get("_temperature", 0.9)
    llm = ChatBedrockConverse(
        model_id=NARRATOR.model, max_tokens=NARRATOR.max_tokens, temperature=temperature
    )

    messages = build_messages_for_character(
        story_lines=state.get("story_lines", []),
        speaker_name=NARRATOR.name,
        other_name=PROTAGONIST.name,
        system_prompt=NARRATOR.system_prompt,
        wind_down=state.get("wind_down", False),
    )

    text = ""
    # Sometimes the LLM might return an empty response, so we retry a few times before giving up
    for _ in range(3):
        response = llm.invoke(messages)
        text = _extract_text(response.content).strip()
        if text:
            break

    return {"narrator_candidates": [text] if text else []}


def narrator_fan_out(state: StoryState) -> list[Send]:
    """Fan out the narrator's turn by creating multiple variations with different temperatures.
    This allows us to explore a range of possible variations for the next story line to explore
    various grammar concepts and word types.
    """
    return [
        Send("narrator_variation", {**state, "_temperature": t})
        for t in [0.2, 0.5, 0.9]
    ]
