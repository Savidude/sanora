"""Lambda handler for invoking the StoryDesigner AgentCore runtime."""

import json
import os
import uuid

import boto3


agentcore_client = boto3.client("bedrock-agentcore")


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
    response_data = json.loads(response_body)

    return response_data
