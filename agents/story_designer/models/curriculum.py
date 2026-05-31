"""Data model for the curriculum."""

from __future__ import annotations

import json
from functools import cached_property
from pathlib import Path

from pydantic import BaseModel, Field


class GrammarConcept(BaseModel):
    """Class containing values of various grammar concepts"""

    code: str
    name: str
    description: str = ""


class WordCategory(BaseModel):
    """Class containing values of various word types"""

    code: str
    name: str
    description: str = ""


class Level(BaseModel):
    """A language level in the curriculum."""

    name: str
    order: int = Field(ge=1)
    grammar_concepts: list[GrammarConcept] = []
    word_categories: list[WordCategory] = []


class Curriculum(BaseModel):
    """Curriculum consisting of multiple language levels."""

    levels: list[Level] = Field(min_length=1)

    @classmethod
    def load(cls) -> Curriculum:
        """Read the hierarchical curriculum folder and return a validated Curriculum."""
        module_dir = Path(__file__).parent.parent  # Go up to story_designer/
        curriculum_path = module_dir / "curriculum"

        levels: list[Level] = []

        for level_dir in sorted(curriculum_path.iterdir()):
            if not level_dir.is_dir():
                continue

            level_file = level_dir / "level.json"
            if not level_file.exists():
                continue

            with open(level_file, encoding="utf-8") as f:
                level_data = json.load(f)

            grammar_concepts = _load_items(
                level_dir / "grammar_concepts", GrammarConcept
            )
            word_categories = _load_items(level_dir / "word_categories", WordCategory)

            levels.append(
                Level(
                    **level_data,
                    grammar_concepts=grammar_concepts,
                    word_categories=word_categories,
                )
            )

        return cls(levels=levels)

    @cached_property
    def grammar_concept_lookup(self) -> dict[str, GrammarConcept]:
        """Lookup dictionary of grammar concepts from curriculum."""
        lookup: dict[str, GrammarConcept] = {}
        for level in self.levels:
            for grammar_concept in level.grammar_concepts:
                lookup[grammar_concept.code] = grammar_concept
        return lookup

    @cached_property
    def word_category_lookup(self) -> dict[str, WordCategory]:
        """Lookup dictionary of word categories from curriculum."""
        lookup: dict[str, WordCategory] = {}
        for level in self.levels:
            for word_category in level.word_categories:
                lookup[word_category.code] = word_category
        return lookup


def _load_items[T](folder: Path, model: type[T]) -> list[T]:
    """Load and validate all JSON files in a folder as instances of *model*."""
    items: list[T] = []
    if not folder.is_dir():
        return items

    for json_file in sorted(folder.iterdir()):
        if json_file.suffix != ".json":
            continue
        with open(json_file, encoding="utf-8") as f:
            items.append(model(**json.load(f)))

    return items
