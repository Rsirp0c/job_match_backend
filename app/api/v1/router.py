from fastapi import APIRouter
from app.api.v1.endpoints import chat, query_agent

router = APIRouter()
router.include_router(chat.router, prefix="/chat", tags=["chat"])
router.include_router(query_agent.router, prefix="/agent", tags=["agent"])

