from langchain_aws import ChatBedrockConverse
from ..characters import Character, LlmModel, build_messages_for_character
from ..state import StoryState

PROTAGONIST = Character(
    name="Protagonist",
    model=LlmModel.AMAZON_NOVA_MICRO,
    max_tokens=64,
    system_prompt=(
        """Yr 1 or 2 short sentences unless 3 are really needed.
        """
    ),
)
