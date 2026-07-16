from __future__ import annotations

from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2_000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    history: List[ChatMessage] = Field(default_factory=list)


class ChatResult(BaseModel):
    type: Literal["place", "post"]
    id: Union[str, int]
    title: str
    category: Optional[str] = None
    address: Optional[str] = None
    tel: Optional[str] = None
    image: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    # 모범음식점 전용 선택 필드
    district: Optional[str] = None
    district_dong: Optional[str] = None
    jibun_address: Optional[str] = None
    main_food: Optional[str] = None
    business_type: Optional[str] = None
    designation_year: Optional[str] = None
    designation_date: Optional[str] = None
    designation_number: Optional[str] = None
    permit_number: Optional[str] = None

    # 서울시 문화행사 전용 선택 필드
    event_type: Optional[str] = None
    event_theme: Optional[str] = None
    event_start_date: Optional[str] = None
    event_end_date: Optional[str] = None
    event_date_text: Optional[str] = None
    event_time: Optional[str] = None
    event_place: Optional[str] = None
    use_fee: Optional[str] = None
    is_free: Optional[str] = None
    target_audience: Optional[str] = None
    inquiry: Optional[str] = None
    organizer: Optional[str] = None
    performer: Optional[str] = None
    program: Optional[str] = None
    homepage_url: Optional[str] = None
    detail_url: Optional[str] = None
    event_status: Optional[str] = None

    # 커뮤니티 게시글 전용 선택 필드
    content_preview: Optional[str] = None
    created_at: Optional[str] = None
    view_count: Optional[int] = None

    # 신뢰성·출처 구분
    source_type: Literal["official", "community"]
    source: str
    source_url: Optional[str] = None
    license: Optional[str] = None
    modified_at: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    results: List[ChatResult] = Field(default_factory=list)
    mode: Literal[
        "openai",
        "local-fallback",
        "no-result",
        "data-limited",
    ]
    query_type: Literal["lookup", "recommend", "search", "post"]
    notice: Optional[str] = None
