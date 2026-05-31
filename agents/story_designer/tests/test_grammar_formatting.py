"""Unit tests for inspector.py helper and formatting functions."""

import pytest

from story_designer.nodes.util import generate_grammar_concept_lines
from story_designer.models.curriculum import GrammarConcept, Curriculum
from story_designer.models.progress import Progress, GrammarConceptProgress


@pytest.fixture
def sample_grammar_concept_lookup() -> dict[str, GrammarConcept]:
    """Fixture providing a sample lookup dictionary of grammar concepts (deprecated).

    This fixture is no longer used as the new generate_grammar_concept_lines
    function builds its own lookup internally using the Curriculum.
    """
    return {
        "personal_pronouns": GrammarConcept(
            code="personal_pronouns",
            name="Personal pronouns",
            description="Pronouns used as a substitute for the proper name of a person. Examples: I, you, he, she, it, we, they.",
        ),
        "to_be_verbs": GrammarConcept(
            code="to_be_verbs",
            name="To be verbs",
            description="Verbs that describe a state of being. Examples: am, is, are, was, were.",
        ),
        "plural": GrammarConcept(
            code="plural",
            name="Plural",
            description="The form of a noun that refers to more than one person or thing. Examples: cat/cats, book/books.",
        ),
    }


# ============================================================================
# Tests for _get_unidentified_grammar_concepts
# ============================================================================


class TestGetUnidentifiedGrammarConcepts:
    """Tests for _get_unidentified_grammar_concepts function."""

    def test_returns_progress_objects(self):
        """Test that the method returns GrammarConceptProgress objects."""
        concepts = [
            GrammarConceptProgress(
                grammar_concept_code="personal_pronouns", identified=False
            )
        ]
        progress = Progress(grammar_concept_progress=concepts)
        result = progress.get_unidentified_grammar_concepts()

        assert len(result) == 1
        assert isinstance(result[0], GrammarConceptProgress)
        assert result[0].grammar_concept_code == "personal_pronouns"

    def test_empty_progress(self):
        """Test with empty progress returns empty list."""
        progress = Progress()
        result = progress.get_unidentified_grammar_concepts()
        assert result == []

    def test_all_concepts_identified(self):
        """Test when all concepts are identified returns empty list."""
        progress = Progress(
            grammar_concept_progress=[
                GrammarConceptProgress(
                    grammar_concept_code="personal_pronouns", identified=True
                ),
                GrammarConceptProgress(
                    grammar_concept_code="to_be_verbs", identified=True
                ),
            ]
        )
        result = progress.get_unidentified_grammar_concepts()
        assert result == []

    def test_all_concepts_unidentified(self):
        """Test when all concepts are unidentified returns all concepts."""
        concepts = [
            GrammarConceptProgress(
                grammar_concept_code="personal_pronouns", identified=False
            ),
            GrammarConceptProgress(
                grammar_concept_code="to_be_verbs", identified=False
            ),
            GrammarConceptProgress(grammar_concept_code="plural", identified=False),
        ]
        progress = Progress(grammar_concept_progress=concepts)
        result = progress.get_unidentified_grammar_concepts()

        assert len(result) == 3
        assert result == concepts

    def test_mixed_identified_and_unidentified(self):
        """Test with mix of identified and unidentified concepts."""
        unidentified_1 = GrammarConceptProgress(
            grammar_concept_code="personal_pronouns", identified=False
        )
        identified = GrammarConceptProgress(
            grammar_concept_code="to_be_verbs", identified=True
        )
        unidentified_2 = GrammarConceptProgress(
            grammar_concept_code="plural", identified=False
        )

        progress = Progress(
            grammar_concept_progress=[unidentified_1, identified, unidentified_2]
        )
        result = progress.get_unidentified_grammar_concepts()

        assert len(result) == 2
        assert unidentified_1 in result
        assert unidentified_2 in result
        assert identified not in result


# ============================================================================
# Tests for _build_grammar_concept_lookup
# ============================================================================


class TestBuildGrammarConceptLookup:
    """Tests for Curriculum.grammar_concept_lookup property."""

    def test_returns_dictionary(self):
        """Test that the property returns a dictionary."""
        curriculum = Curriculum.load()
        result = curriculum.grammar_concept_lookup
        assert isinstance(result, dict)

    def test_keys_are_strings(self):
        """Test that all keys in the lookup are strings."""
        curriculum = Curriculum.load()
        result = curriculum.grammar_concept_lookup
        assert all(isinstance(key, str) for key in result.keys())

    def test_values_are_grammar_concepts(self):
        """Test that all values in the lookup are GrammarConcept objects."""
        curriculum = Curriculum.load()
        result = curriculum.grammar_concept_lookup
        assert all(isinstance(value, GrammarConcept) for value in result.values())

    def test_keys_match_grammar_concept_codes(self):
        """Test that dictionary keys match the code of their values."""
        curriculum = Curriculum.load()
        result = curriculum.grammar_concept_lookup
        for code, concept in result.items():
            assert code == concept.code

    def test_contains_expected_level_1_concepts(self):
        """Test that lookup contains grammar concepts from level 1."""
        curriculum = Curriculum.load()
        result = curriculum.grammar_concept_lookup

        # Check for some level 1 concepts
        assert "personal_pronouns" in result
        assert "to_be_verbs" in result

        assert result["personal_pronouns"].name == "Personal pronouns"
        assert result["to_be_verbs"].name == "To be verbs"

    def test_contains_expected_level_2_concepts(self):
        """Test that lookup contains grammar concepts from level 2."""
        curriculum = Curriculum.load()
        result = curriculum.grammar_concept_lookup

        # Check for some level 2 concepts
        assert "negative_sentences" in result
        assert result["negative_sentences"].name == "Negative sentences"

    def test_contains_expected_level_3_concepts(self):
        """Test that lookup contains grammar concepts from level 3."""
        curriculum = Curriculum.load()
        result = curriculum.grammar_concept_lookup

        # Check for some level 3 concepts
        assert "plural" in result
        assert "possessive_case" in result

    def test_no_duplicate_codes(self):
        """Test that there are no duplicate concept codes across levels."""
        curriculum = Curriculum.load()
        result = curriculum.grammar_concept_lookup

        # The length of the dictionary should equal the number of unique concepts
        # This is guaranteed by dictionary behavior, but we verify conceptually
        codes = [concept.code for concept in result.values()]
        assert len(codes) == len(set(codes))

    def test_all_concepts_have_description(self):
        """Test that all concepts in the lookup have descriptions."""
        curriculum = Curriculum.load()
        result = curriculum.grammar_concept_lookup

        for concept in result.values():
            assert hasattr(concept, "description")
            # Description can be empty but should exist
            assert concept.description is not None

    def test_lookup_contains_multiple_levels(self):
        """Test that the lookup contains concepts from multiple levels."""
        curriculum = Curriculum.load()
        result = curriculum.grammar_concept_lookup

        # Get a sample of concepts from different levels
        level_1_concepts = {"personal_pronouns", "to_be_verbs"}
        level_2_concepts = {"negative_sentences"}
        level_3_concepts = {"plural", "possessive_case"}

        found_level_1 = any(code in result for code in level_1_concepts)
        found_level_2 = any(code in result for code in level_2_concepts)
        found_level_3 = any(code in result for code in level_3_concepts)

        assert found_level_1
        assert found_level_2
        assert found_level_3

    def test_concept_code_and_name_consistency(self):
        """Test that concept codes and names are present and consistent."""
        curriculum = Curriculum.load()
        result = curriculum.grammar_concept_lookup

        for code, concept in result.items():
            # Code should not be empty
            assert code
            # Concept should have a name
            assert concept.name
            # Name should not be empty
            assert len(concept.name) > 0


# ============================================================================
# Tests for generate_grammar_concept_lines
# ============================================================================


class TestGenerateGrammarLines:
    """Tests for generate_grammar_concept_lines function."""

    def test_with_empty_concepts(self):
        """Test that empty list of unidentified concepts returns empty list."""
        result = generate_grammar_concept_lines([])
        assert result == []

    def test_single_concept(self):
        """Test with a single unidentified concept."""
        unidentified_concepts = [
            GrammarConceptProgress(grammar_concept_code="personal_pronouns")
        ]
        result = generate_grammar_concept_lines(unidentified_concepts)

        assert len(result) == 1
        # Should contain the concept code and description from curriculum
        assert "personal_pronouns" in result[0]
        assert result[0].startswith("- personal_pronouns: ")

    def test_multiple_concepts(self):
        """Test with multiple unidentified concepts."""
        unidentified_concepts = [
            GrammarConceptProgress(grammar_concept_code="personal_pronouns"),
            GrammarConceptProgress(grammar_concept_code="to_be_verbs"),
        ]
        result = generate_grammar_concept_lines(unidentified_concepts)

        assert len(result) == 2
        assert all("- " in line and ": " in line for line in result)
        assert "personal_pronouns" in result[0]
        assert "to_be_verbs" in result[1]

    def test_concept_not_in_curriculum(self):
        """Test that concepts not in curriculum are skipped."""
        unidentified_concepts = [
            GrammarConceptProgress(grammar_concept_code="personal_pronouns"),
            GrammarConceptProgress(grammar_concept_code="nonexistent_concept_xyz"),
        ]
        result = generate_grammar_concept_lines(unidentified_concepts)

        # Should only include the concept that exists in curriculum
        assert len(result) == 1
        assert "personal_pronouns" in result[0]

    def test_format_structure(self):
        """Test that the output format is '- code: description'."""
        unidentified_concepts = [
            GrammarConceptProgress(grammar_concept_code="personal_pronouns"),
        ]
        result = generate_grammar_concept_lines(unidentified_concepts)

        assert len(result) == 1
        line = result[0]
        # Verify format: starts with "- ", contains code and description separated by ": "
        assert line.startswith("- "), "Line should start with '- '"
        assert ": " in line, "Line should contain ': ' separator"
        parts = line.split(": ", 1)
        assert len(parts) == 2, "Line should have exactly one ': ' separator"

    def test_return_type(self):
        """Test that the return type is always a list of strings."""
        unidentified_concepts = [
            GrammarConceptProgress(grammar_concept_code="personal_pronouns"),
        ]
        result = generate_grammar_concept_lines(unidentified_concepts)

        assert isinstance(result, list)
        assert all(isinstance(item, str) for item in result)
