from pathlib import Path

from langchain_aws import ChatBedrockConverse
from .narrator import NARRATOR
from ..characters import Character, LlmModel, build_messages_for_character
from ..state import StoryState

PROTAGONIST = Character(
    name="Protagonist",
    model=LlmModel.AMAZON_NOVA_MICRO,
    max_tokens=64,
)


def _extract_text(content) -> str:
    if isinstance(content, str):
        return content
    return "".join(
        block.get("text", "") if isinstance(block, dict) else str(block)
        for block in content
    )


def _get_system_prompt_for_protagonist() -> str:
    """Return the system prompt for the protagonist."""
    protagonist_prompt_path = (
        Path(__file__).parent.parent / "prompts" / "protagonist_prompt.md"
    )
    return protagonist_prompt_path.read_text(encoding="utf-8")


def protagonist_turn(state: StoryState) -> dict:
    """Build the history of the story for the protagonist's turn, invoke the protagonist's LLM to
    generate a new story line, and return it as part of the updated story lines.
    """

    llm = ChatBedrockConverse(
        model_id=PROTAGONIST.model, max_tokens=PROTAGONIST.max_tokens
    )

    messages = build_messages_for_character(
        story_lines=state.get("story_lines", []),
        speaker_name=PROTAGONIST.name,
        other_name=NARRATOR.name,
        system_prompt=_get_system_prompt_for_protagonist(),
    )

    raw_text = ""
    # Sometimes the LLM might return an empty response, so we retry a few times before giving up
    for _ in range(3):
        response = llm.invoke(messages)
        raw_text = _extract_text(response.content)
        if raw_text.strip():
            break

    if not raw_text.strip():
        raise RuntimeError("Protagonist model returned empty text after 3 attempts")

    display_text = raw_text.strip()
    story_line = f"{PROTAGONIST.name}: {display_text}"
    new_story_lines = list(state.get("story_lines", [])) + [story_line]

    return {
        "story_lines": new_story_lines,
    }
