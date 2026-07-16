from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any, List

# 공공데이터 응답 스키마
class LocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: str
    title: str
    addr1: Optional[str] = None
    addr2: Optional[str] = None
    tel: Optional[str] = None
    mapx: Optional[float] = None
    mapy: Optional[float] = None
    firstimage: Optional[str] = None
    extra_data: Optional[Any] = None

class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    title: str
    content: str
    views: int
    tags: Optional[str] = None
    created_at: datetime

# 게시글 생성 스키마
class PostCreate(BaseModel):
    category: str
    title: str
    content: str
    password: str
    tags: Optional[str] = None

# 게시글 수정 스키마
class PostUpdate(BaseModel):
    title: str
    content: str
    password: str
    tags: Optional[str] = None

# 게시글 삭제 검증 스키마
class PostDelete(BaseModel):
    password: str

# 게시글 권한 검증 스키마
class PasswordVerifyRequest(BaseModel):
    password: str

class PasswordVerifyResponse(BaseModel):
    authorized: bool

# 게시글 목록용 요약 응답 스키마 (본문 제외)
class PostSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    title: str
    views: int
    tags: Optional[str] = None
    created_at: datetime

# 게시글 상세 조회용 응답 스키마 (본문 포함)
class PostDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    title: str
    content: str
    views: int
    tags: Optional[str] = None
    created_at: datetime

class PageMeta(BaseModel):
    total_count: int      # 전체 데이터 개수
    page: int             # 현재 페이지 번호
    size: int             # 한 페이지당 데이터 개수
    total_pages: int      # 전체 페이지 수
    has_next: bool        # 다음 페이지 존재 여부
    has_prev: bool        # 이전 페이지 존재 여부

class PaginatedLocationResponse(BaseModel):
    items: List[LocationResponse]
    meta: PageMeta

class PaginatedPostResponse(BaseModel):
    items: List[PostResponse]
    meta: PageMeta