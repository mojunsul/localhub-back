from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.database import get_db
from app.models import Location
# PaginatedLocationResponse와 PageMeta 임포트 추가
from app.schemas import LocationResponse, PaginatedLocationResponse, PageMeta

router = APIRouter(prefix="/api/locations", tags=["Locations"])

@router.get("", response_model=PaginatedLocationResponse)
def get_locations(
    category_id: Optional[str] = Query(None, description="콘텐츠 유형 ID 필터링"),
    keyword: Optional[str] = Query(None, description="키워드 검색 (장소명/주소 통합)"),
    title: Optional[str] = Query(None, description="장소명으로 검색"),
    address: Optional[str] = Query(None, description="주소로 검색"),
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(9, ge=1, description="한 페이지당 아이템 개수 (기본 9개)"),
    db: Session = Depends(get_db)
):
    query = db.query(Location)
    
    if category_id:
        query = query.filter(Location.category_id == category_id)
    if title:
        query = query.filter(Location.title.like(f"%{title}%"))
    if address:
        query = query.filter(Location.addr1.like(f"%{address}%"))
    if keyword:
        query = query.filter(
            (Location.title.like(f"%{keyword}%")) | 
            (Location.addr1.like(f"%{keyword}%"))
        )
    
    # 1. 전체 개수 계산
    total_count = query.count()
    
    # 2. 페이징 쿼리 적용 (9개씩 offset 계산)
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()
    
    # 3. 메타데이터 산출
    total_pages = math.ceil(total_count / size) if total_count > 0 else 1
    
    return PaginatedLocationResponse(
        items=items,
        meta=PageMeta(
            total_count=total_count,
            page=page,
            size=size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
    )