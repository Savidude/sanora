"""Endpoints for the messaging application."""

from fastapi import FastAPI
import uvicorn

from .v1 import v1_router
from .config.middleware import default_fastapi_middleware

app = FastAPI(
    title="Messaging API",
    description="API endpoint invoking AWS Agentcore messaging services.",
)
# app.add_middleware(default_fastapi_middleware())
app.include_router(v1_router, prefix="/api")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
