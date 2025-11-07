"""
Version 1 of the messaging API
"""

from fastapi import APIRouter
from .api.chat import chat_router

v1_router = APIRouter(prefix="/v1", tags=["v1"])
v1_router.include_router(chat_router)
