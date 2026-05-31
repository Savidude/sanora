"""Unit tests for decider.py node."""

import pytest

from story_designer.nodes.decider import (
    decider,
    _score_phrase,
    _get_identified_grammar_concepts,
)
from story_designer.models.content import Phrase, PhraseAnalysis, GrammarFinding
from story_designer.models.progress import Progress, GrammarConceptProgress
from story_designer.state import StoryState
from story_designer.nodes.narrator import NARRATOR


# ============================================================================
# Fixtures for reusable test data
# ============================================================================


@pytest.fixture
def personal_pronouns_finding():
    """Fixture for a personal pronouns grammar finding."""
    return GrammarFinding(grammar_concept_code="personal_pronouns", matched_text="I")


@pytest.fixture
def to_be_verbs_finding():
    """Fixture for a to_be_verbs grammar finding."""
    return GrammarFinding(grammar_concept_code="to_be_verbs", matched_text="am")


@pytest.fixture
def verb_forms_finding():
    """Fixture for a verb_forms grammar finding."""
    return GrammarFinding(grammar_concept_code="verb_forms", matched_text="learning")


@pytest.fixture
def phrase_with_personal_pronouns(personal_pronouns_finding):
    """Fixture for a phrase with personal pronouns finding."""
    return Phrase(
        content="I am happy",
        analysis=PhraseAnalysis(grammar_findings=[personal_pronouns_finding]),
    )


@pytest.fixture
def phrase_with_two_findings(personal_pronouns_finding, to_be_verbs_finding):
    """Fixture for a phrase with personal pronouns and to_be_verbs findings."""
    return Phrase(
        content="I am here",
        analysis=PhraseAnalysis(
            grammar_findings=[personal_pronouns_finding, to_be_verbs_finding]
        ),
    )


@pytest.fixture
def phrase_with_three_findings(
    personal_pronouns_finding, to_be_verbs_finding, verb_forms_finding
):
    """Fixture for a phrase with three findings."""
    return Phrase(
        content="We are learning",
        analysis=PhraseAnalysis(
            grammar_findings=[
                personal_pronouns_finding,
                to_be_verbs_finding,
                verb_forms_finding,
            ]
        ),
    )


@pytest.fixture
def phrase_empty_analysis():
    """Fixture for a phrase with empty analysis."""
    return Phrase(content="Test content", analysis=PhraseAnalysis(grammar_findings=[]))


@pytest.fixture
def progress_all_unidentified():
    """Fixture for progress with all concepts unidentified."""
    return Progress(
        grammar_concept_progress=[
            GrammarConceptProgress(
                grammar_concept_code="personal_pronouns", identified=False
            ),
            GrammarConceptProgress(
                grammar_concept_code="to_be_verbs", identified=False
            ),
            GrammarConceptProgress(grammar_concept_code="verb_forms", identified=False),
        ]
    )


@pytest.fixture
def progress_mixed_identification():
    """Fixture for progress with mixed identified/unidentified concepts."""
    return Progress(
        grammar_concept_progress=[
            GrammarConceptProgress(
                grammar_concept_code="personal_pronouns", identified=True
            ),
            GrammarConceptProgress(
                grammar_concept_code="to_be_verbs", identified=False
            ),
            GrammarConceptProgress(grammar_concept_code="verb_forms", identified=False),
        ]
    )


@pytest.fixture
def progress_personal_pronouns_unidentified():
    """Fixture for progress with only personal pronouns unidentified."""
    return Progress(
        grammar_concept_progress=[
            GrammarConceptProgress(
                grammar_concept_code="personal_pronouns", identified=False
            )
        ]
    )


@pytest.fixture
def progress_personal_pronouns_identified():
    """Fixture for progress with only personal pronouns identified."""
    return Progress(
        grammar_concept_progress=[
            GrammarConceptProgress(
                grammar_concept_code="personal_pronouns", identified=True
            )
        ]
    )


@pytest.fixture
def empty_progress():
    """Fixture for empty progress."""
    return Progress()


# ============================================================================
# Test Classes
# ============================================================================


class TestGetIdentifiedGrammarConcepts:
    """Tests for _get_identified_grammar_concepts helper function."""

    def test_single_analysis_single_finding(self, personal_pronouns_finding):
        """Test extracting grammar concepts from a phrase with one analysis and one finding."""
        phrase = Phrase(
            content="Test content",
            analysis=PhraseAnalysis(grammar_findings=[personal_pronouns_finding]),
        )
        concepts = _get_identified_grammar_concepts(phrase)
        assert concepts == ["personal_pronouns"]

    def test_single_analysis_multiple_findings(
        self, personal_pronouns_finding, to_be_verbs_finding
    ):
        """Test extracting grammar concepts from a phrase with multiple findings."""
        phrase = Phrase(
            content="Test content",
            analysis=PhraseAnalysis(
                grammar_findings=[personal_pronouns_finding, to_be_verbs_finding]
            ),
        )
        concepts = _get_identified_grammar_concepts(phrase)
        assert set(concepts) == {"personal_pronouns", "to_be_verbs"}

    def test_multiple_findings_in_single_analysis(
        self, personal_pronouns_finding, to_be_verbs_finding
    ):
        """Test extracting grammar concepts from a single phrase analysis with multiple findings."""
        phrase = Phrase(
            content="Test content",
            analysis=PhraseAnalysis(
                grammar_findings=[personal_pronouns_finding, to_be_verbs_finding]
            ),
        )
        concepts = _get_identified_grammar_concepts(phrase)
        assert set(concepts) == {"personal_pronouns", "to_be_verbs"}

    def test_no_findings(self):
        """Test with phrase analysis that has no findings."""
        phrase = Phrase(
            content="Test content", analysis=PhraseAnalysis(grammar_findings=[])
        )
        concepts = _get_identified_grammar_concepts(phrase)
        assert concepts == []

    def test_empty_phrase_analysis(self, phrase_empty_analysis):
        """Test with phrase that has an empty analysis."""
        concepts = _get_identified_grammar_concepts(phrase_empty_analysis)
        assert concepts == []


class TestScorePhrase:
    """Tests for _score_phrase helper function."""

    def test_score_single_newly_identified_concept(
        self, phrase_with_personal_pronouns, progress_personal_pronouns_unidentified
    ):
        """Test scoring a phrase with one newly identified grammar concept."""
        score = _score_phrase(
            phrase_with_personal_pronouns, progress_personal_pronouns_unidentified
        )
        assert score == 1

    def test_score_multiple_newly_identified_concepts(
        self, phrase_with_two_findings, progress_all_unidentified
    ):
        """Test scoring a phrase with multiple newly identified concepts."""
        score = _score_phrase(phrase_with_two_findings, progress_all_unidentified)
        assert score == 2

    def test_score_already_identified_concept(
        self, phrase_with_personal_pronouns, progress_personal_pronouns_identified
    ):
        """Test that already identified concepts don't increase the score."""
        score = _score_phrase(
            phrase_with_personal_pronouns, progress_personal_pronouns_identified
        )
        assert score == 0

    def test_score_mixed_identified_and_unidentified(
        self, phrase_with_two_findings, progress_mixed_identification
    ):
        """Test scoring with a mix of identified and unidentified concepts."""
        score = _score_phrase(phrase_with_two_findings, progress_mixed_identification)
        assert score == 1

    def test_score_no_findings(self, phrase_empty_analysis):
        """Test scoring a phrase with no findings."""
        progress = Progress()
        score = _score_phrase(phrase_empty_analysis, progress)
        assert score == 0


class TestDecider:
    """Tests for the main decider function."""

    def test_selects_phrase_with_highest_score(
        self,
        phrase_with_personal_pronouns,
        phrase_with_two_findings,
        progress_all_unidentified,
    ):
        """Test that decider selects the phrase with the highest score."""
        state: StoryState = {
            "messages": [],
            "story_lines": [],
            "narrator_candidates": [],
            "inspector_results": [
                phrase_with_personal_pronouns,
                phrase_with_two_findings,
            ],
            "progress": progress_all_unidentified,
            "wind_down": False,
        }

        result = decider(state)

        # phrase_with_two_findings should be selected because it has score of 2 vs score of 1
        assert (
            f"{NARRATOR.name}: {phrase_with_two_findings.content}"
            in result["story_lines"]
        )

    def test_appends_to_existing_story_lines(
        self, phrase_with_personal_pronouns, progress_personal_pronouns_unidentified
    ):
        """Test that the new story line is appended to existing ones."""
        state: StoryState = {
            "messages": [],
            "story_lines": ["Line 1", "Line 2"],
            "narrator_candidates": [],
            "inspector_results": [phrase_with_personal_pronouns],
            "progress": progress_personal_pronouns_unidentified,
            "wind_down": False,
        }

        result = decider(state)

        assert len(result["story_lines"]) == 3
        assert result["story_lines"][0] == "Line 1"
        assert result["story_lines"][1] == "Line 2"
        assert (
            f"{NARRATOR.name}: {phrase_with_personal_pronouns.content}"
            == result["story_lines"][2]
        )

    def test_clears_narrator_candidates(
        self, phrase_with_personal_pronouns, progress_personal_pronouns_unidentified
    ):
        """Test that narrator_candidates are set to None in the result."""
        state: StoryState = {
            "messages": [],
            "story_lines": [],
            "narrator_candidates": ["candidate1", "candidate2"],
            "inspector_results": [phrase_with_personal_pronouns],
            "progress": progress_personal_pronouns_unidentified,
            "wind_down": False,
        }

        result = decider(state)

        assert result["narrator_candidates"] is None

    def test_clears_inspector_results(
        self, phrase_with_personal_pronouns, progress_personal_pronouns_unidentified
    ):
        """Test that inspector_results are set to None in the result."""
        state: StoryState = {
            "messages": [],
            "story_lines": [],
            "narrator_candidates": [],
            "inspector_results": [phrase_with_personal_pronouns],
            "progress": progress_personal_pronouns_unidentified,
            "wind_down": False,
        }

        result = decider(state)

        assert result["inspector_results"] is None

    def test_single_phrase(
        self, phrase_with_personal_pronouns, progress_personal_pronouns_unidentified
    ):
        """Test with a single phrase in inspector_results."""
        state: StoryState = {
            "messages": [],
            "story_lines": [],
            "narrator_candidates": [],
            "inspector_results": [phrase_with_personal_pronouns],
            "progress": progress_personal_pronouns_unidentified,
            "wind_down": False,
        }

        result = decider(state)

        assert len(result["story_lines"]) == 1
        assert (
            f"{NARRATOR.name}: {phrase_with_personal_pronouns.content}"
            == result["story_lines"][0]
        )

    def test_raises_error_with_no_inspector_results(self, empty_progress):
        """Test that decider raises an error when inspector_results is empty."""
        state: StoryState = {
            "messages": [],
            "story_lines": [],
            "narrator_candidates": [],
            "inspector_results": [],
            "progress": empty_progress,
            "wind_down": False,
        }

        with pytest.raises(
            ValueError, match="decider reached with no inspector_results"
        ):
            decider(state)

    def test_raises_error_with_missing_inspector_results(self, empty_progress):
        """Test that decider raises an error when inspector_results key is missing."""
        state: StoryState = {
            "messages": [],
            "story_lines": [],
            "narrator_candidates": [],
            "inspector_results": [],
            "progress": empty_progress,
            "wind_down": False,
        }
        # Remove inspector_results by getting an empty list
        state_copy = {k: v for k, v in state.items() if k != "inspector_results"}

        with pytest.raises(
            ValueError, match="decider reached with no inspector_results"
        ):
            decider(state_copy)

    def test_tie_breaking_selects_first_best(
        self, personal_pronouns_finding, progress_personal_pronouns_unidentified
    ):
        """Test that when multiple phrases have the same score, one is selected."""
        phrase1 = Phrase(
            content="First phrase",
            analysis=PhraseAnalysis(grammar_findings=[personal_pronouns_finding]),
        )
        phrase2 = Phrase(
            content="Second phrase",
            analysis=PhraseAnalysis(grammar_findings=[personal_pronouns_finding]),
        )
        state: StoryState = {
            "messages": [],
            "story_lines": [],
            "narrator_candidates": [],
            "inspector_results": [phrase1, phrase2],
            "progress": progress_personal_pronouns_unidentified,
            "wind_down": False,
        }

        result = decider(state)

        # One of them should be selected
        assert len(result["story_lines"]) == 1
        selected_content = result["story_lines"][0]
        assert selected_content in [
            f"{NARRATOR.name}: First phrase",
            f"{NARRATOR.name}: Second phrase",
        ]

    def test_complex_scenario_with_multiple_phrases(
        self,
        personal_pronouns_finding,
        to_be_verbs_finding,
        verb_forms_finding,
        progress_mixed_identification,
    ):
        """Test a realistic scenario with multiple phrases and progress."""
        phrase1 = Phrase(
            content="I am Finnish",
            analysis=PhraseAnalysis(grammar_findings=[personal_pronouns_finding]),
        )
        phrase2 = Phrase(
            content="You are here",
            analysis=PhraseAnalysis(grammar_findings=[to_be_verbs_finding]),
        )
        phrase3 = Phrase(
            content="We are learning",
            analysis=PhraseAnalysis(
                grammar_findings=[
                    personal_pronouns_finding,
                    to_be_verbs_finding,
                    verb_forms_finding,
                ]
            ),
        )
        state: StoryState = {
            "messages": [],
            "story_lines": ["Once upon a time..."],
            "narrator_candidates": [],
            "inspector_results": [phrase1, phrase2, phrase3],
            "progress": progress_mixed_identification,
            "wind_down": False,
        }

        result = decider(state)

        # phrase3 should be selected because it has 2 new concepts (to_be_verbs, verb_forms)
        # phrase1 has 0 (personal_pronouns already identified)
        # phrase2 has 1 (to_be_verbs)
        assert len(result["story_lines"]) == 2
        assert f"{NARRATOR.name}: We are learning" == result["story_lines"][1]

    def test_preserves_existing_data(
        self, phrase_with_personal_pronouns, progress_personal_pronouns_unidentified
    ):
        """Test that existing state data is not lost."""
        state: StoryState = {
            "messages": [],
            "story_lines": ["Line 1"],
            "narrator_candidates": [],
            "inspector_results": [phrase_with_personal_pronouns],
            "progress": progress_personal_pronouns_unidentified,
            "wind_down": False,
        }

        result = decider(state)

        # Original state should not be modified
        assert state["story_lines"] == ["Line 1"]
        assert len(result["story_lines"]) == 2
