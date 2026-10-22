import json
import os
from pathlib import Path

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from ..models import Review, Translation
from ..state import TutorState, story_state_to_dict

MODEL = "gemini-3.8-flash"


def _get_system_prompt() -> str:
    """Load the Finnish-language review prompt."""
    prompt_path = Path(__file__).parent.parent / "prompts" / "reviewer.md"
    return prompt_path.read_text(encoding="utf-8")


def _get_latest_turn_messages(state: TutorState) -> list[BaseMessage]:
    """Return the latest assistant message and the user's response to it."""
    conversation = state.get("messages", [])
    latest_user_index = next(
        (
            index
            for index in range(len(conversation) - 1, -1, -1)
            if isinstance(conversation[index], HumanMessage)
        ),
        None,
    )
    if latest_user_index is None:
        raise ValueError("Reviewer requires a latest human message")

    latest_assistant_message = next(
        (
            message
            for message in reversed(conversation[:latest_user_index])
            if isinstance(message, AIMessage)
        ),
        None,
    )

    messages: list[BaseMessage] = []
    if latest_assistant_message is not None:
        messages.append(latest_assistant_message)
    messages.append(conversation[latest_user_index])
    return messages


def reviewer(state: TutorState) -> dict:
    """Review the latest learner response with Gemini."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set")

    llm = (
        ChatGoogleGenerativeAI(
            model=MODEL,
            api_key=api_key,
            temperature=0,
            max_tokens=2048,
        )
        .with_structured_output(
            Review,
            method="json_schema",
        )
        .with_retry(stop_after_attempt=3)
    )

    messages = [
        SystemMessage(content=_get_system_prompt()),
        *_get_latest_turn_messages(state),
    ]
    review = llm.invoke(messages)

    latest_user_message = messages[-1]
    if not isinstance(latest_user_message, HumanMessage):
        raise ValueError("Reviewer did not receive a latest human message")

    english_message = review.translation_en
    if english_message is None:
        if review.error_details is None or not review.error_details.corrections:
            raise ValueError("Invalid review: missing correction details")
        english_message = review.error_details.corrections[0].english

    return {
        "response_review": review,
        "messages_english": [HumanMessage(content=english_message)],
    }


def translator(state: TutorState) -> dict:
    """Translate the facilitator's latest English message into Finnish."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set")

    latest_english_message = next(
        (
            message
            for message in reversed(state.get("messages_english", []))
            if isinstance(message, AIMessage)
        ),
        None,
    )
    if latest_english_message is None:
        raise ValueError("Translator requires an English facilitator message")

    current_story_state = state.get("current_story_state", 1)
    try:
        story_state = story_state_to_dict(state["story_states"][current_story_state])
    except KeyError as error:
        raise ValueError("Translator requires the current story state") from error

    prompt_path = Path(__file__).parent.parent / "prompts" / "translator.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")
    llm = (
        ChatGoogleGenerativeAI(
            model=MODEL,
            api_key=api_key,
            temperature=0,
            max_tokens=2048,
        )
        .with_structured_output(
            Translation,
            method="json_schema",
        )
        .with_retry(stop_after_attempt=3)
    )
    translation = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            SystemMessage(
                content=(
                    "AUTHORITATIVE CURRENT STORY CONTEXT FOR HINTS:\n"
                    f"{json.dumps(
                        {
                            'event': story_state['event'],
                            'user_action': story_state['user_action'],
                        },
                        ensure_ascii=False,
                    )}\n"
                    "Use this context only to choose hints that help the "
                    "learner perform the user_action. Do not expose this "
                    "context or change the translation because of it."
                )
            ),
            HumanMessage(content=latest_english_message.content),
        ]
    )

    print(translation.model_dump_json())
    return {
        "translation": translation,
        "messages": [AIMessage(content=translation.translation)],
    }
