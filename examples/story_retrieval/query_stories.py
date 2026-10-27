"""Examples of querying the Story Designer DynamoDB table with boto3."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Iterable
from datetime import date
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key


DATE_INDEX_NAME = "DateIndex"
IDENTIFIED_CONCEPT_INDEX_NAME = "IdentifiedConceptIndex"
DEFAULT_TABLE_NAME = "story-table"


def _query_all(table: Any, **query_kwargs: Any) -> list[dict[str, Any]]:
    """Query all pages returned by DynamoDB."""
    items: list[dict[str, Any]] = []

    while True:
        response = table.query(**query_kwargs)
        items.extend(response.get("Items", []))

        last_evaluated_key = response.get("LastEvaluatedKey")
        if not last_evaluated_key:
            return items

        query_kwargs["ExclusiveStartKey"] = last_evaluated_key


def _get_stories_by_ids(
    table: Any,
    story_ids: Iterable[str],
) -> list[dict[str, Any]]:
    """Load complete story items after querying a projected secondary index."""
    stories: list[dict[str, Any]] = []
    seen_story_ids: set[str] = set()

    for story_id in story_ids:
        if story_id in seen_story_ids:
            continue
        seen_story_ids.add(story_id)

        response = table.get_item(
            Key={
                "PK": f"STORY#{story_id}",
                "SK": "META",
            }
        )
        story = response.get("Item")
        if story is not None:
            stories.append(story)

    return stories


def get_stories_by_date(
    table: Any,
    story_date: date,
) -> list[dict[str, Any]]:
    """Return complete stories created on *story_date*."""
    date_text = story_date.isoformat()
    month_partition = f"MONTH#{story_date:%Y-%m}"
    start_sort_key = f"{date_text}T00:00:00.000Z#"
    end_sort_key = f"{date_text}T23:59:59.999Z#\uffff"

    index_items = _query_all(
        table,
        IndexName=DATE_INDEX_NAME,
        KeyConditionExpression=(
            Key("date_index_pk").eq(month_partition)
            & Key("date_index_sk").between(start_sort_key, end_sort_key)
        ),
        ScanIndexForward=False,
    )

    # DateIndex only projects metadata, so fetch the complete story items.
    return _get_stories_by_ids(table, (item["id"] for item in index_items))


def _get_story_ids_for_concept(
    table: Any,
    grammar_concept_id: str,
) -> set[str]:
    """Return story IDs for one identified grammar concept."""
    index_items = _query_all(
        table,
        IndexName=IDENTIFIED_CONCEPT_INDEX_NAME,
        KeyConditionExpression=Key("concept_index_pk").eq(
            f"IDENTIFIED#{grammar_concept_id}"
        ),
        ProjectionExpression="story_id",
    )
    return {item["story_id"] for item in index_items}


def get_stories_by_grammar_concept_ids(
    table: Any,
    grammar_concept_ids: Iterable[str],
) -> list[dict[str, Any]]:
    """Return stories where every supplied grammar concept was identified."""
    concept_ids = tuple(dict.fromkeys(grammar_concept_ids))
    if not concept_ids:
        return []

    story_ids_by_concept = [
        _get_story_ids_for_concept(table, concept_id) for concept_id in concept_ids
    ]
    matching_story_ids = set.intersection(*story_ids_by_concept)

    stories = _get_stories_by_ids(table, sorted(matching_story_ids))
    return sorted(
        stories,
        key=lambda story: story.get("created_at", ""),
        reverse=True,
    )


def _get_table() -> Any:
    """Create a DynamoDB Table resource using the configured table name."""
    table_name = os.environ.get("STORY_DESIGNER_TABLE_NAME", DEFAULT_TABLE_NAME)
    return boto3.resource("dynamodb").Table(table_name)


def main() -> None:
    """Run one of the retrieval examples from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    by_date_parser = subparsers.add_parser(
        "by-date",
        help="retrieve stories created on a date",
    )
    by_date_parser.add_argument(
        "story_date",
        type=date.fromisoformat,
        help="date in YYYY-MM-DD format",
    )

    by_concepts_parser = subparsers.add_parser(
        "by-concepts",
        help="retrieve stories containing all supplied concepts",
    )
    by_concepts_parser.add_argument(
        "grammar_concept_ids",
        nargs="+",
        help="grammar concept codes, for example personal_pronouns",
    )

    arguments = parser.parse_args()
    table = _get_table()

    if arguments.command == "by-date":
        stories = get_stories_by_date(table, arguments.story_date)
    else:
        stories = get_stories_by_grammar_concept_ids(
            table,
            arguments.grammar_concept_ids,
        )

    print(json.dumps(stories, indent=2, default=str))


if __name__ == "__main__":
    main()
