"""Story designer agent entrypoint."""

import json
import os

import boto3
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from story_designer.graph import graph

app = BedrockAgentCoreApp()


def _load_gemini_api_key() -> None:
    """Load the Gemini API key from Secrets Manager for the AgentCore runtime.

    Local development can continue to provide GEMINI_API_KEY directly. In AWS,
    only the secret ARN is configured as an environment variable; the secret
    value is fetched using the runtime execution role.
    """
    secret_arn = os.getenv("GEMINI_API_KEY_SECRET_ARN")
    if not secret_arn or os.getenv("GEMINI_API_KEY"):
        return

    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_arn)
    secret_string = response.get("SecretString")
    if not secret_string:
        raise RuntimeError("The Gemini API key secret has no SecretString value")

    try:
        secret_value = json.loads(secret_string)
    except json.JSONDecodeError:
        api_key = secret_string
    else:
        if not isinstance(secret_value, dict):
            raise RuntimeError(
                "The Gemini API key secret must contain plaintext or a JSON object"
            )
        api_key = secret_value.get("GEMINI_API_KEY") or secret_value.get("api_key")

    if not api_key:
        raise RuntimeError(
            "The Gemini API key secret must contain GEMINI_API_KEY or api_key"
        )
    os.environ["GEMINI_API_KEY"] = api_key


_load_gemini_api_key()


@app.entrypoint
def invoke(payload: dict) -> dict:
    """Invoke the story designer agent."""
    prompt = payload.get("prompt", "").strip()
    if not prompt:
        raise ValueError("payload.prompt is required")
    result = graph.invoke(
        {
            "story_opening": prompt,
        }
    )
    return {
        "message": result.get("full_story", ""),
        "story_lines": result.get("story_lines", []),
    }


if __name__ == "__main__":
    app.run()
