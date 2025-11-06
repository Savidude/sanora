"""Endpoints for the messaging application."""

import json
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import uvicorn
import boto3

from models.comms import PromptRequest, ResponseData, AgentResponse

app = FastAPI(
    title="Messaging API",
    description="API endpoint invoking AWS Agentcore messaging services.",
)
client = boto3.client("bedrock-agentcore", region_name="eu-central-1")

# CORS configuration allowing specific local origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1|0\.0\.0\.0|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2[0-9]|3[0-1])\.\d{1,3}\.\d{1,3}):3000$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/v1/chat/message", response_model=AgentResponse)
async def invoke_agent(request: PromptRequest):
    """
    Invoke AWS Bedrock agent with the provided prompt

    Args:
        request (PromptRequest): The prompt request containing message and session ID.
    """

    try:
        payload = json.dumps({"prompt": request.message})
        session_id = f"session_{request.sessionId}"

        # Invoke agent runtime
        response = client.invoke_agent_runtime(
            agentRuntimeArn="arn:aws:bedrock-agentcore:eu-central-1:442042519937:runtime/finnish_tutor-ojM3Y4CG44",
            runtimeSessionId=session_id,
            payload=payload,
            qualifier="DEFAULT",
        )

        response_body = response["response"].read()
        response_data = json.loads(response_body)
        agent_response_str = response_data["content"][0]["text"]
        agent_response_json = json.loads(agent_response_str)

        return AgentResponse(
            success=True,
            data=ResponseData(teacherResponse=agent_response_json),
            session_id=session_id,
            timestamp=datetime.now(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error invoking agent: {str(e)}"
        ) from e


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
