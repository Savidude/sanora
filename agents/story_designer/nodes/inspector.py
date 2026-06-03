"""Inspector node implementation for analyzing candidate story lines and providing insights on
grammar concepts and word categories.
"""

from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.types import Send

from ..state import StoryState
from ..models.progress import Progress
from ..models.content import Phrase, PhraseAnalysis
from .util import generate_grammar_concept_lines, generate_word_category_lines


def _load_inspector_template() -> str:
    """Load the inspector prompt template from file."""
    template_path = (
        Path(__file__).parent.parent / "prompts" / "inspector_prompt_template.md"
    )
    return template_path.read_text(encoding="utf-8")


def _populate_template(
    template: str, grammar_lines: list[str], word_category_lines: list[str]
) -> str:
    """Replace placeholder tags in template with generated content."""
    result = template.replace("<GRAMMAR_CONCEPTS>", "\n".join(grammar_lines))
    result = result.replace("<WORD_CATEGORIES>", "\n".join(word_category_lines))
    return result


def _generate_inspector_system_prompt(progress: Progress) -> str:
    """Generate the inspector system prompt with curriculum-based content."""
    # Gather grammar concepts
    unidentified_grammar_concepts = progress.get_unidentified_grammar_concepts()
    grammar_lines = generate_grammar_concept_lines(unidentified_grammar_concepts)

    # Gather word categories
    least_identified_word_categories = progress.get_least_identified_word_categories()
    word_category_lines = generate_word_category_lines(least_identified_word_categories)

    # Load template and populate with content
    template = _load_inspector_template()
    return _populate_template(template, grammar_lines, word_category_lines)


def inspector_fan_out(state: StoryState) -> list[Send]:
    """Fan out the inspector node for each narrator candidate."""
    candidates = state.get("narrator_candidates", [])
    return [Send("inspector", {**state, "_candidate_text": c}) for c in candidates]


def inspector(state: StoryState) -> dict:
    """Run the inspector LLM to analyze the candidate story line and produce insights for the
    identified grammar concepts and word categories.
    """
    candidate_text = state.get("_candidate_text", "")
    system_prompt = _generate_inspector_system_prompt(state["progress"])

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite-preview",
    ).with_structured_output(PhraseAnalysis)

    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=candidate_text),
        ]
    )

    phrase = Phrase(content=candidate_text, analysis=response)
    return {
        "inspector_results": [phrase],
    }
