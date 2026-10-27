# Story retrieval examples

These examples use the DynamoDB table created by
`AgentMessagingStack`.

The table name defaults to `story-table`, or can be overridden with
`STORY_DESIGNER_TABLE_NAME`.

```bash
export AWS_REGION=eu-central-1
export STORY_DESIGNER_TABLE_NAME=story-table
```

Retrieve stories created on a specific date:

```bash
python examples/story_retrieval/query_stories.py by-date 2026-10-27
```

Retrieve stories where all listed grammar concepts were identified:

```bash
python examples/story_retrieval/query_stories.py \
  by-concepts personal_pronouns verb_forms
```

The concept query performs one query per grammar concept against
`IdentifiedConceptIndex`, then intersects the returned story IDs.
