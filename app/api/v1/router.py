from fastapi import APIRouter
from app.api.v1.endpoints import chat_stream, query_agent, vector_search

router = APIRouter()
router.include_router(chat_stream.router, prefix="/chat", tags=["chat"])
router.include_router(vector_search.router, prefix="/vector", tags=["vector"])
router.include_router(query_agent.router, prefix="/agent", tags=["agent"])

