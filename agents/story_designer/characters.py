from enum import Enum
from pydantic import BaseModel

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

WIND_DOWN_INSTRUCTION = """
WIND-DOWN PHASE:
The story is now approaching its end. Steer the next turn toward a satisfying
conclusion — a moment of resolution, revelation, or meaningful choice. Do not
introduce new mysteries, side characters, or unresolved threads. Bring the
emotional arc to a close naturally over the next turn or two.
"""


class LlmModel(str, Enum):
    """Enum for supported LLM models that play the role of characters"""

    OPENAI_GPT_OSS_20B = "openai.gpt-oss-20b-1:0"
    AMAZON_NOVA_MICRO = "eu.amazon.nova-micro-v1:0"


class Character(BaseModel):
    """A character in the story."""

    name: str
    model: LlmModel
    max_tokens: int = 256
    system_prompt: str


def _build_system_prompt(system_prompt: str, wind_down: bool) -> str:
    if wind_down:
        return f"{system_prompt}\n\n{WIND_DOWN_INSTRUCTION}"
    return system_prompt


def build_messages_for_character(
    story_lines: list[str],
    speaker_name: str,
    other_name: str,
    system_prompt: str,
    wind_down: bool,
) -> list:
    """Build a history of messages for a character's turn based on the current story lines.
    Previous messages sent by the character are portrayed as AI messages, while messages from
    the other character are portrayed as human messages.

    That is, if the speaker is the Narrator, then its messages are AIMessage and the Protagonist's
    messages are HumanMessage, and vice versa if the speaker is the Protagonist.

    This ensures that the character's LLM receives the correct conversational context to generate
    its next turn, while also keeping the system prompt separate and consistent. This is
    essentially "ticking" each LLM into thinking that it is talking to a human.

    The system prompt is augmented with wind-down instructions if the story is approaching its
    conclusion.
    """

    messages = [SystemMessage(content=_build_system_prompt(system_prompt, wind_down))]

    # story_lines[0] is the opening scene — add as human context
    if story_lines:
        messages.append(HumanMessage(content=story_lines[0]))

    for line in story_lines[1:]:
        if line.startswith(f"{speaker_name}:"):
            content = line[len(f"{speaker_name}:") :].strip()
            messages.append(AIMessage(content=content))
        elif line.startswith(f"{other_name}:"):
            content = line[len(f"{other_name}:") :].strip()
            messages.append(HumanMessage(content=content))

    return messages
