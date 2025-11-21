"""middleware helpers for application"""

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware import Middleware


def default_fastapi_middleware() -> Middleware:
    """default middleware config for FastAPI"""
    return Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
