"""Unit tests for aggregator.py node."""

import pytest

from story_designer.nodes.aggregator import aggregator
from story_designer.models.content import (
    PhraseAnalysis,
    GrammarFinding,
    WordFinding,
)
from story_designer.models.progress import (
    Progress,
    GrammarConceptProgress,
    WordCategoryProgress,
)
from story_designer.state import StoryState
from langchain_core.messages import HumanMessage


# ============================================================================
# Fixtures for reusable test data
# ============================================================================


@pytest.fixture
def grammar_finding_personal_pronouns():
    """Fixture for a personal pronouns grammar finding."""
    return GrammarFinding(grammar_concept_code="personal_pronouns", matched_text="I")


@pytest.fixture
def grammar_finding_to_be_verbs():
    """Fixture for a to_be_verbs grammar finding."""
    return GrammarFinding(grammar_concept_code="to_be_verbs", matched_text="am")


@pytest.fixture
def grammar_finding_verb_forms():
    """Fixture for a verb_forms grammar finding."""
    return GrammarFinding(grammar_concept_code="verb_forms", matched_text="learning")


@pytest.fixture
def word_finding_greetings():
    """Fixture for a greetings word finding."""
    return WordFinding(word_category_code="word_greetings", matched_text="hello")


@pytest.fixture
def word_finding_numbers():
    """Fixture for a numbers word finding."""
    return WordFinding(word_category_code="word_numbers", matched_text="five")


@pytest.fixture
def empty_phrase_analysis():
    """Fixture for an empty phrase analysis."""
    return PhraseAnalysis(grammar_findings=[], word_findings=[])


@pytest.fixture
def phrase_analysis_single_grammar(grammar_finding_personal_pronouns):
    """Fixture for phrase analysis with a single grammar finding."""
    return PhraseAnalysis(
        grammar_findings=[grammar_finding_personal_pronouns], word_findings=[]
    )


@pytest.fixture
def phrase_analysis_multiple_grammar(
    grammar_finding_personal_pronouns, grammar_finding_to_be_verbs
):
    """Fixture for phrase analysis with multiple grammar findings."""
    return PhraseAnalysis(
        grammar_findings=[
            grammar_finding_personal_pronouns,
            grammar_finding_to_be_verbs,
        ],
        word_findings=[],
    )


@pytest.fixture
def phrase_analysis_single_word(word_finding_greetings):
    """Fixture for phrase analysis with a single word finding."""
    return PhraseAnalysis(grammar_findings=[], word_findings=[word_finding_greetings])


@pytest.fixture
def phrase_analysis_multiple_word(word_finding_greetings, word_finding_numbers):
    """Fixture for phrase analysis with multiple word findings."""
    return PhraseAnalysis(
        grammar_findings=[],
        word_findings=[word_finding_greetings, word_finding_numbers],
    )


@pytest.fixture
def phrase_analysis_mixed(
    grammar_finding_personal_pronouns,
    grammar_finding_to_be_verbs,
    word_finding_greetings,
    word_finding_numbers,
):
    """Fixture for phrase analysis with both grammar and word findings."""
    return PhraseAnalysis(
        grammar_findings=[
            grammar_finding_personal_pronouns,
            grammar_finding_to_be_verbs,
        ],
        word_findings=[word_finding_greetings, word_finding_numbers],
    )


@pytest.fixture
def progress_empty():
    """Fixture for progress with no concepts."""
    return Progress(grammar_concept_progress=[], word_category_progress=[])


@pytest.fixture
def progress_single_grammar():
    """Fixture for progress with a single grammar concept."""
    return Progress(
        grammar_concept_progress=[
            GrammarConceptProgress(grammar_concept_code="personal_pronouns")
        ],
        word_category_progress=[],
    )


@pytest.fixture
def progress_multiple_grammar():
    """Fixture for progress with multiple grammar concepts."""
    return Progress(
        grammar_concept_progress=[
            GrammarConceptProgress(grammar_concept_code="personal_pronouns"),
            GrammarConceptProgress(grammar_concept_code="to_be_verbs"),
            GrammarConceptProgress(grammar_concept_code="verb_forms"),
        ],
        word_category_progress=[],
    )


@pytest.fixture
def progress_single_word():
    """Fixture for progress with a single word category."""
    return Progress(
        grammar_concept_progress=[],
        word_category_progress=[
            WordCategoryProgress(word_category_code="word_greetings")
        ],
    )


@pytest.fixture
def progress_multiple_word():
    """Fixture for progress with multiple word categories."""
    return Progress(
        grammar_concept_progress=[],
        word_category_progress=[
            WordCategoryProgress(word_category_code="word_greetings"),
            WordCategoryProgress(word_category_code="word_numbers"),
        ],
    )


@pytest.fixture
def progress_mixed():
    """Fixture for progress with both grammar and word categories."""
    return Progress(
        grammar_concept_progress=[
            GrammarConceptProgress(grammar_concept_code="personal_pronouns"),
            GrammarConceptProgress(grammar_concept_code="to_be_verbs"),
        ],
        word_category_progress=[
            WordCategoryProgress(word_category_code="word_greetings"),
            WordCategoryProgress(word_category_code="word_numbers"),
        ],
    )


@pytest.fixture
def base_story_state():
    """Fixture for a basic story state with empty analysis."""
    return StoryState(
        messages=[HumanMessage(content="test")],
        story_lines=[],
        narrator_candidates=[],
        inspector_results=[],
        progress=Progress(),
        pending_analyses=PhraseAnalysis(),
        wind_down=False,
    )


# ============================================================================
# Test: aggregator with empty findings
# ============================================================================


def test_aggregator_empty_findings(progress_single_grammar):
    """Test that aggregator handles empty findings gracefully."""
    state: StoryState = {
        "messages": [HumanMessage(content="test")],
        "story_lines": [],
        "narrator_candidates": [],
        "inspector_results": [],
        "progress": progress_single_grammar,
        "pending_analyses": PhraseAnalysis(grammar_findings=[], word_findings=[]),
        "wind_down": False,
    }

    # Assert initial state
    assert progress_single_grammar.grammar_concept_progress[0].total_findings == 0
    assert progress_single_grammar.grammar_concept_progress[0].identified is False

    result = aggregator(state)

    # Should return a dict (though aggregator doesn't explicitly return anything)
    assert isinstance(result, (dict, type(None)))
    # Progress should remain unchanged (no findings)
    assert progress_single_grammar.grammar_concept_progress[0].total_findings == 0
    assert progress_single_grammar.grammar_concept_progress[0].identified is False


# ============================================================================
# Test: aggregator with single grammar finding
# ============================================================================


def test_aggregator_single_grammar_finding(
    progress_single_grammar, phrase_analysis_single_grammar
):
    """Test that aggregator updates progress for a single grammar finding."""
    state: StoryState = {
        "messages": [HumanMessage(content="test")],
        "story_lines": [],
        "narrator_candidates": [],
        "inspector_results": [],
        "progress": progress_single_grammar,
        "pending_analyses": phrase_analysis_single_grammar,
        "wind_down": False,
    }

    # Assert initial state
    assert progress_single_grammar.grammar_concept_progress[0].total_findings == 0
    assert progress_single_grammar.grammar_concept_progress[0].identified is False

    aggregator(state)

    # Check that grammar progress was updated
    assert progress_single_grammar.grammar_concept_progress[0].total_findings == 1
    assert progress_single_grammar.grammar_concept_progress[0].identified is True


# ============================================================================
# Test: aggregator with multiple grammar findings
# ============================================================================


def test_aggregator_multiple_grammar_findings(
    progress_multiple_grammar, phrase_analysis_multiple_grammar
):
    """Test that aggregator updates progress for multiple grammar findings."""
    state: StoryState = {
        "messages": [HumanMessage(content="test")],
        "story_lines": [],
        "narrator_candidates": [],
        "inspector_results": [],
        "progress": progress_multiple_grammar,
        "pending_analyses": phrase_analysis_multiple_grammar,
        "wind_down": False,
    }

    # Assert initial state
    assert progress_multiple_grammar.grammar_concept_progress[0].total_findings == 0
    assert progress_multiple_grammar.grammar_concept_progress[1].total_findings == 0

    aggregator(state)

    # Check that both grammar concepts were updated
    assert progress_multiple_grammar.grammar_concept_progress[0].total_findings == 1
    assert progress_multiple_grammar.grammar_concept_progress[0].identified is True
    assert progress_multiple_grammar.grammar_concept_progress[1].total_findings == 1
    assert progress_multiple_grammar.grammar_concept_progress[1].identified is True


# ============================================================================
# Test: aggregator with single word finding
# ============================================================================


def test_aggregator_single_word_finding(
    progress_single_word, phrase_analysis_single_word
):
    """Test that aggregator updates progress for a single word finding."""
    state: StoryState = {
        "messages": [HumanMessage(content="test")],
        "story_lines": [],
        "narrator_candidates": [],
        "inspector_results": [],
        "progress": progress_single_word,
        "pending_analyses": phrase_analysis_single_word,
        "wind_down": False,
    }

    # Assert initial state
    assert progress_single_word.word_category_progress[0].total_occurrences == 0

    aggregator(state)

    # Check that word category progress was updated
    assert progress_single_word.word_category_progress[0].total_occurrences == 1


# ============================================================================
# Test: aggregator with multiple word findings
# ============================================================================


def test_aggregator_multiple_word_findings(
    progress_multiple_word, phrase_analysis_multiple_word
):
    """Test that aggregator updates progress for multiple word findings."""
    state: StoryState = {
        "messages": [HumanMessage(content="test")],
        "story_lines": [],
        "narrator_candidates": [],
        "inspector_results": [],
        "progress": progress_multiple_word,
        "pending_analyses": phrase_analysis_multiple_word,
        "wind_down": False,
    }

    # Assert initial state
    assert progress_multiple_word.word_category_progress[0].total_occurrences == 0
    assert progress_multiple_word.word_category_progress[1].total_occurrences == 0

    aggregator(state)

    # Check that both word categories were updated
    assert progress_multiple_word.word_category_progress[0].total_occurrences == 1
    assert progress_multiple_word.word_category_progress[1].total_occurrences == 1


# ============================================================================
# Test: aggregator with mixed findings
# ============================================================================


def test_aggregator_mixed_findings(progress_mixed, phrase_analysis_mixed):
    """Test that aggregator updates progress for both grammar and word findings."""
    state: StoryState = {
        "messages": [HumanMessage(content="test")],
        "story_lines": [],
        "narrator_candidates": [],
        "inspector_results": [],
        "progress": progress_mixed,
        "pending_analyses": phrase_analysis_mixed,
        "wind_down": False,
    }

    # Assert initial state
    assert progress_mixed.grammar_concept_progress[0].total_findings == 0
    assert progress_mixed.grammar_concept_progress[1].total_findings == 0
    assert progress_mixed.word_category_progress[0].total_occurrences == 0
    assert progress_mixed.word_category_progress[1].total_occurrences == 0

    aggregator(state)

    # Check that both grammar concepts were updated
    assert progress_mixed.grammar_concept_progress[0].total_findings == 1
    assert progress_mixed.grammar_concept_progress[0].identified is True
    assert progress_mixed.grammar_concept_progress[1].total_findings == 1
    assert progress_mixed.grammar_concept_progress[1].identified is True

    # Check that both word categories were updated
    assert progress_mixed.word_category_progress[0].total_occurrences == 1
    assert progress_mixed.word_category_progress[1].total_occurrences == 1


# ============================================================================
# Test: aggregator with duplicate findings (same concept/category appears
# multiple times in findings)
# ============================================================================


def test_aggregator_duplicate_grammar_findings(progress_multiple_grammar):
    """Test that aggregator correctly aggregates duplicate grammar findings."""
    # Create analysis with duplicate grammar concepts
    duplicate_findings = PhraseAnalysis(
        grammar_findings=[
            GrammarFinding(grammar_concept_code="personal_pronouns", matched_text="I"),
            GrammarFinding(grammar_concept_code="personal_pronouns", matched_text="we"),
        ],
        word_findings=[],
    )

    state: StoryState = {
        "messages": [HumanMessage(content="test")],
        "story_lines": [],
        "narrator_candidates": [],
        "inspector_results": [],
        "progress": progress_multiple_grammar,
        "pending_analyses": duplicate_findings,
        "wind_down": False,
    }

    # Assert initial state
    assert progress_multiple_grammar.grammar_concept_progress[0].total_findings == 0

    aggregator(state)

    # The same concept should be counted twice
    assert progress_multiple_grammar.grammar_concept_progress[0].total_findings == 2


def test_aggregator_duplicate_word_findings(progress_multiple_word):
    """Test that aggregator correctly aggregates duplicate word findings."""
    # Create analysis with duplicate word categories
    duplicate_findings = PhraseAnalysis(
        grammar_findings=[],
        word_findings=[
            WordFinding(word_category_code="word_greetings", matched_text="hello"),
            WordFinding(word_category_code="word_greetings", matched_text="hi"),
        ],
    )

    state: StoryState = {
        "messages": [HumanMessage(content="test")],
        "story_lines": [],
        "narrator_candidates": [],
        "inspector_results": [],
        "progress": progress_multiple_word,
        "pending_analyses": duplicate_findings,
        "wind_down": False,
    }

    # Assert initial state
    assert progress_multiple_word.word_category_progress[0].total_occurrences == 0

    aggregator(state)

    # The same category should be counted twice
    assert progress_multiple_word.word_category_progress[0].total_occurrences == 2


# ============================================================================
# Test: aggregator with existing progress values
# ============================================================================


def test_aggregator_accumulates_grammar_findings():
    """Test that aggregator accumulates findings to existing progress."""
    progress = Progress(
        grammar_concept_progress=[
            GrammarConceptProgress(
                grammar_concept_code="personal_pronouns",
                total_findings=5,
                identified=True,
            ),
        ],
        word_category_progress=[],
    )

    analysis = PhraseAnalysis(
        grammar_findings=[
            GrammarFinding(grammar_concept_code="personal_pronouns", matched_text="I"),
        ],
        word_findings=[],
    )

    state: StoryState = {
        "messages": [HumanMessage(content="test")],
        "story_lines": [],
        "narrator_candidates": [],
        "inspector_results": [],
        "progress": progress,
        "pending_analyses": analysis,
        "wind_down": False,
    }

    # Assert initial state
    assert progress.grammar_concept_progress[0].total_findings == 5

    aggregator(state)

    # Should accumulate to existing findings
    assert progress.grammar_concept_progress[0].total_findings == 6


def test_aggregator_accumulates_word_findings():
    """Test that aggregator accumulates findings to existing word category progress."""
    progress = Progress(
        grammar_concept_progress=[],
        word_category_progress=[
            WordCategoryProgress(
                word_category_code="word_greetings", total_occurrences=3
            ),
        ],
    )

    analysis = PhraseAnalysis(
        grammar_findings=[],
        word_findings=[
            WordFinding(word_category_code="word_greetings", matched_text="hello"),
        ],
    )

    state: StoryState = {
        "messages": [HumanMessage(content="test")],
        "story_lines": [],
        "narrator_candidates": [],
        "inspector_results": [],
        "progress": progress,
        "pending_analyses": analysis,
        "wind_down": False,
    }

    # Assert initial state
    assert progress.word_category_progress[0].total_occurrences == 3

    aggregator(state)

    # Should accumulate to existing occurrences
    assert progress.word_category_progress[0].total_occurrences == 4


# ============================================================================
# Test: aggregator with multiple findings across different concepts
# ============================================================================


def test_aggregator_multiple_concepts_different_counts():
    """Test that aggregator correctly counts different concepts with different counts."""
    progress = Progress(
        grammar_concept_progress=[
            GrammarConceptProgress(grammar_concept_code="personal_pronouns"),
            GrammarConceptProgress(grammar_concept_code="to_be_verbs"),
            GrammarConceptProgress(grammar_concept_code="verb_forms"),
        ],
        word_category_progress=[],
    )

    analysis = PhraseAnalysis(
        grammar_findings=[
            GrammarFinding(grammar_concept_code="personal_pronouns", matched_text="I"),
            GrammarFinding(
                grammar_concept_code="personal_pronouns", matched_text="you"
            ),
            GrammarFinding(grammar_concept_code="to_be_verbs", matched_text="am"),
            GrammarFinding(grammar_concept_code="to_be_verbs", matched_text="is"),
            GrammarFinding(grammar_concept_code="to_be_verbs", matched_text="are"),
        ],
        word_findings=[],
    )

    state: StoryState = {
        "messages": [HumanMessage(content="test")],
        "story_lines": [],
        "narrator_candidates": [],
        "inspector_results": [],
        "progress": progress,
        "pending_analyses": analysis,
        "wind_down": False,
    }

    # Assert initial state
    assert progress.grammar_concept_progress[0].total_findings == 0
    assert progress.grammar_concept_progress[1].total_findings == 0
    assert progress.grammar_concept_progress[2].total_findings == 0

    aggregator(state)

    # Check that each concept has the correct count
    assert progress.grammar_concept_progress[0].total_findings == 2  # personal_pronouns
    assert progress.grammar_concept_progress[1].total_findings == 3  # to_be_verbs
    assert (
        progress.grammar_concept_progress[2].total_findings == 0
    )  # verb_forms (not in findings)


# ============================================================================
# Test: aggregator doesn't modify state unrelated to progress
# ============================================================================


def test_aggregator_doesnt_modify_unrelated_state(
    progress_single_grammar, phrase_analysis_single_grammar
):
    """Test that aggregator only modifies progress, not other state fields."""
    original_story_lines = ["Once upon a time"]
    original_narrator_candidates = ["character_1"]

    state: StoryState = {
        "messages": [HumanMessage(content="test")],
        "story_lines": original_story_lines.copy(),
        "narrator_candidates": original_narrator_candidates.copy(),
        "inspector_results": [],
        "progress": progress_single_grammar,
        "pending_analyses": phrase_analysis_single_grammar,
        "wind_down": False,
    }

    aggregator(state)

    # Verify other state fields weren't modified
    assert state["story_lines"] == original_story_lines
    assert state["narrator_candidates"] == original_narrator_candidates
    assert state["wind_down"] is False
