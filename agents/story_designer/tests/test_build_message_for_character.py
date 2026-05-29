"""Unit tests for build_messages_for_character function in characters.py."""

import pytest

from characters import build_messages_for_character
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

NARRATOR_NAME = "Narrator"
PROTAGONIST_NAME = "Protagonist"
NARRATOR_SYSTEM_PROMPT = "Test Narrator system prompt."
PROTAGONIST_SYSTEM_PROMPT = "Test Protagonist system prompt."


@pytest.fixture
def opening_scene_only() -> list[str]:
    """Fixture for story lines with only the opening scene and no previous messages
    from the Narrator."""
    return ["Test opening scene."]


def test_build_messages_for_character_with_opening_scene_only(opening_scene_only):
    """Test that the opening scene is correctly added as a human message and there are no
    AI messages when there are no previous messages from the Narrator."""
    # messages before the Narrator's turn
    messaages = build_messages_for_character(
        story_lines=opening_scene_only,
        speaker_name=NARRATOR_NAME,
        other_name=PROTAGONIST_NAME,
        system_prompt=NARRATOR_SYSTEM_PROMPT,
        wind_down=False,
    )

    assert len(messaages) == 2
    assert isinstance(messaages[0], SystemMessage)
    assert messaages[0].content == NARRATOR_SYSTEM_PROMPT
    assert isinstance(messaages[1], HumanMessage)
    assert messaages[1].content == opening_scene_only[0]


@pytest.fixture
def one_narrator_message() -> list[str]:
    """Fixture for story lines with the opening scene and one previous message
    from the Narrator."""
    return [
        "Test opening scene.",
        f"{NARRATOR_NAME}: The protagonist walks into a room.",
    ]


def test_build_messages_for_character_with_one_narrator_message(one_narrator_message):
    """Test that the opening scene is correctly added as a human message and the
    previous Narrator message is correctly added as an AI message when there is one
    previous message from the Narrator, for the Protagonist's turn."""
    # messages for before Protagonist's response
    messaages = build_messages_for_character(
        story_lines=one_narrator_message,
        speaker_name=PROTAGONIST_NAME,
        other_name=NARRATOR_NAME,
        system_prompt=PROTAGONIST_SYSTEM_PROMPT,
        wind_down=False,
    )

    assert len(messaages) == 3
    assert isinstance(messaages[0], SystemMessage)
    assert messaages[0].content == PROTAGONIST_SYSTEM_PROMPT
    assert isinstance(messaages[1], HumanMessage)
    assert (
        messaages[1].content == one_narrator_message[0]
    )  # opening scene as human message
    assert isinstance(messaages[2], HumanMessage)
    assert (
        messaages[2].content
        == one_narrator_message[1][len(f"{NARRATOR_NAME}:") :].strip()
    )  # narrator message as human message


@pytest.fixture
def one_protagonist_message() -> list[str]:
    """Fixture for story lines with the opening scene, one previous message from the
    Narrator, and one previous message from the Protagonist."""
    return [
        "Test opening scene.",
        f"{NARRATOR_NAME}: The protagonist walks into a room.",
        f"{PROTAGONIST_NAME}: Wow. What a lovely room. I sure hope I don't get stabbed.",
    ]


def test_build_messages_for_character_with_one_protagonist_message(
    one_protagonist_message,
):
    """Test that the opening scene is correctly added as a human message, the previous
    Narrator message is correctly added as an AI message, and the previous
    Protagonist message is correctly added as a human message when there is one
    previous message from the Narrator and one previous message from the Protagonist,
    for the Narrator's turn."""
    # messages for the Narrator's next turn in response to the Protagonist's message
    messaages = build_messages_for_character(
        story_lines=one_protagonist_message,
        speaker_name=NARRATOR_NAME,
        other_name=PROTAGONIST_NAME,
        system_prompt=NARRATOR_SYSTEM_PROMPT,
        wind_down=False,
    )

    assert len(messaages) == 4
    assert isinstance(messaages[0], SystemMessage)
    assert messaages[0].content == NARRATOR_SYSTEM_PROMPT
    assert isinstance(messaages[1], HumanMessage)
    assert (
        messaages[1].content == one_protagonist_message[0]
    )  # opening scene as human message
    assert isinstance(messaages[2], AIMessage)
    assert (
        messaages[2].content
        == one_protagonist_message[1][len(f"{NARRATOR_NAME}:") :].strip()
    )  # narrator message as AI message
    assert isinstance(messaages[3], HumanMessage)
    assert (
        messaages[3].content
        == one_protagonist_message[2][len(f"{PROTAGONIST_NAME}:") :].strip()
    )  # protagonist message as human message


def test_wind_down_in_system_prompt(one_protagonist_message):
    """Test that the system prompt is correctly augmented with wind-down instructions"""
    # system prompt should be augmented with wind-down instructions when wind_down=True
    messages = build_messages_for_character(
        story_lines=[one_protagonist_message],
        speaker_name=NARRATOR_NAME,
        other_name=PROTAGONIST_NAME,
        system_prompt=NARRATOR_SYSTEM_PROMPT,
        wind_down=True,
    )

    assert isinstance(messages[0], SystemMessage)
    assert NARRATOR_SYSTEM_PROMPT in messages[0].content
    assert "WIND-DOWN PHASE" in messages[0].content
