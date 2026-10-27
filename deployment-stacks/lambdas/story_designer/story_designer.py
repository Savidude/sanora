"""Lambda handler for invoking the StoryDesigner AgentCore runtime."""

import json
import os
import uuid
from datetime import datetime, timezone

import boto3
from botocore.config import Config
from sanora_contracts import StoryDesignerResponse


agentcore_client = boto3.client(
    "bedrock-agentcore",
    config=Config(
        connect_timeout=10,
        read_timeout=540,
        retries={"mode": "standard", "total_max_attempts": 1},
    ),
)
s3_client = boto3.client("s3")


def _store_story_response(
    response_data: StoryDesignerResponse,
    story_id: str,
    created_at: str,
    story_object_path: str,
) -> None:
    """Store a story response and its identified grammar concept indexes."""
    story_pk = f"STORY#{story_id}"

    story_item = response_data.model_dump(
        mode="json",
        exclude={"story_states", "grammar_progress"},
    )
    story_item.update(
        {
            "PK": story_pk,
            "SK": "META",
            "entity_type": "STORY",
            "id": story_id,
            "created_at": created_at,
            "date_index_pk": f"MONTH#{created_at[:7]}",
            "date_index_sk": f"{created_at}#{story_id}",
        }
    )
    story_item["story_object_path"] = story_object_path

    table = boto3.resource("dynamodb").Table(os.environ["STORY_DESIGNER_TABLE_NAME"])
    with table.batch_writer() as batch:
        batch.put_item(Item=story_item)

        for grammar_concept in response_data.grammar_progress:
            concept_item = {
                "PK": story_pk,
                "SK": f"CONCEPT#{grammar_concept.grammar_concept_code}",
                "entity_type": "GRAMMAR_CONCEPT",
                "story_id": story_id,
                "grammar_concept_code": grammar_concept.grammar_concept_code,
                "identified": grammar_concept.identified,
                "created_at": created_at,
                "story_object_path": story_object_path,
            }
            if grammar_concept.identified:
                concept_item.update(
                    {
                        "concept_index_pk": (
                            f"IDENTIFIED#{grammar_concept.grammar_concept_code}"
                        ),
                        "concept_index_sk": f"{created_at}#{story_id}",
                    }
                )
            batch.put_item(Item=concept_item)


def handler(event: dict, context: object) -> dict:
    """Invoke the StoryDesigner runtime and return its response."""
    prompt = event.get("prompt", "").strip()
    if not prompt:
        raise ValueError("event.prompt is required")

    response = agentcore_client.invoke_agent_runtime(
        agentRuntimeArn=os.environ["STORY_DESIGNER_RUNTIME_ARN"],
        runtimeSessionId=f"story-designer-{uuid.uuid4().hex}",
        payload=json.dumps({"prompt": prompt}),
        qualifier="DEFAULT",
    )

    response_body = response["response"].read()
    response_data = StoryDesignerResponse.model_validate(json.loads(response_body))
    story_id = str(uuid.uuid4().hex)
    created_at = (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )
    story_object_path = f"{created_at[:10]}/{story_id}.json"
    story_states = response_data.model_dump(mode="json")["story_states"]

    s3_client.put_object(
        Bucket=os.environ["STORY_DESIGNER_BUCKET_NAME"],
        Key=story_object_path,
        Body=json.dumps(story_states).encode("utf-8"),
        ContentType="application/json",
    )
    _store_story_response(
        response_data,
        story_id,
        created_at,
        story_object_path,
    )

    return response_data.model_dump(mode="json")
