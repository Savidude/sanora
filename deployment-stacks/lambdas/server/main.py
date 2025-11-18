"""Endpoints for the messaging application.

To run locally, invoke:
```
uvicorn server:app --reload
```
"""

from fastapi import FastAPI
from mangum import Mangum

from v1 import v1_router
from config.middleware import default_fastapi_middleware
from config.logger import configure_logger


app = FastAPI(
    title="Messaging API",
    description="API endpoint invoking AWS Agentcore messaging services.",
    middleware=[default_fastapi_middleware()],
)
configure_logger(__name__)

# app.add_middleware(default_fastapi_middleware())
app.include_router(v1_router, prefix="/api")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)

handler = Mangum(app)
