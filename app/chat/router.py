from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException

from .data_loader import DataLoadError
from .post_search_adapter import search_posts_for_chat
from .schemas import ChatRequest, ChatResponse
from .service import ChatService, PostSearcher


router = APIRouter(prefix="/api", tags=["chat"])
_service = ChatService(post_searcher=search_posts_for_chat)


def set_post_searcher(
    searcher: Optional[PostSearcher],
) -> None:
    """
    일반 백엔드가 만든 게시글 검색 함수를 연결한다.

    함수 형식:
        search_posts(question: str, limit: int) -> 게시글 목록
    """
    _service.set_post_searcher(searcher)


@router.get("/chat/health")
def chat_health() -> dict:
    try:
        return _service.health()
    except DataLoadError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        return await _service.answer(request)
    except DataLoadError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc
