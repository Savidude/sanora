"""Utility functions for the Story Designer nodes"""

from ..models.progress import GrammarConceptProgress, WordCategoryProgress


def generate_grammar_concept_lines(
    unidentified_concepts: list[GrammarConceptProgress],
) -> list[str]:
    """Generate formatted strings for unidentified grammar concepts."""
    from .orchestration import CURRICULUM

    lookup = CURRICULUM.grammar_concept_lookup
    return [
        f"- {concept.code}: {concept.description}"
        for gc in unidentified_concepts
        if (concept := lookup.get(gc.grammar_concept_code))
    ]


def generate_word_category_lines(categories: list[WordCategoryProgress]) -> list[str]:
    """Generate formatted strings for least identified word categories."""
    from .orchestration import CURRICULUM

    lookup = CURRICULUM.word_category_lookup
    return [
        f"- {category.code}: {category.description}"
        for wc in categories
        if (category := lookup.get(wc.word_category_code))
    ]


def extract_text(content) -> str:
    """Extract text from the model response content."""
    if isinstance(content, str):
        return content
    parts = []
    for block in content:
        if not isinstance(block, dict):
            parts.append(str(block))
            continue
        if "reasoning_content" in block:
            continue  # skip CoT on purpose
        parts.append(block.get("text", ""))
    return "".join(parts)
