from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from app.database import get_db
from app.models import Post
from app.schemas import (
    PasswordVerifyRequest,
    PasswordVerifyResponse,
    PostCreate,
    PostUpdate,
    PostDelete,
    PostSummaryResponse,
    PostDetailResponse,
    PostResponse,
    PaginatedPostResponse,
    PageMeta,
)
import math

router = APIRouter(prefix="/api/posts", tags=["Posts"])

# ==========================================
# [챗봇 협업 연동] 공용 최신글 검색 유틸 함수
# ==========================================
def search_posts(db: Session, keyword: str, limit: int = 5) -> List[Post]:
    """
    챗봇 담당 팀원이 사용할 공유 검색 함수입니다.
    게시글의 제목, 본문, 태그를 대상으로 검색을 수행합니다.
    """
    return db.query(Post).filter(
        or_(
            Post.title.like(f"%{keyword}%"),
            Post.content.like(f"%{keyword}%"),
            Post.tags.like(f"%{keyword}%")
        )
    ).order_by(Post.created_at.desc()).limit(limit).all()


# ==========================================
# 익명 게시판 CRUD API 엔드포인트 구현부
# ==========================================

@router.get("", response_model=PaginatedPostResponse)
def get_posts(
    keyword: Optional[str] = Query(None, description="제목, 본문, 태그 통합 검색"),
    title: Optional[str] = Query(None, description="제목으로 검색"),
    content: Optional[str] = Query(None, description="본문으로 검색"),
    tag: Optional[str] = Query(None, description="태그로 검색"),
    category: Optional[str] = Query(None, description="카테고리로 검색"),
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(10, ge=1, description="한 페이지당 아이템 개수 (기본 10개)"),
    db: Session = Depends(get_db)
):
    # 최신 등록 순서대로 정렬하기 위해 desc() 정렬을 적용합니다.
    query = db.query(Post).order_by(Post.id.desc())

    if title:
        query = query.filter(Post.title.like(f"%{title}%"))

    if content:
        query = query.filter(Post.content.like(f"%{content}%"))

    if tag:
        query = query.filter(Post.tags.like(f"%{tag}%"))

    if category:
        query = query.filter(Post.category == category)

    if keyword:
        query = query.filter(
            or_(
                Post.title.like(f"%{keyword}%"),
                Post.content.like(f"%{keyword}%"),
                Post.tags.like(f"%{keyword}%")
            )
        )
    
    # 1. 전체 개수 계산
    total_count = query.count()
    
    # 2. 페이징 쿼리 적용 (10개씩 offset 계산)
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()
    
    # 3. 메타데이터 산출
    total_pages = math.ceil(total_count / size) if total_count > 0 else 1
    
    return PaginatedPostResponse(
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


@router.get("/popular", response_model=List[PostResponse])
def get_popular_posts(
    # 기본값(default)을 5에서 2로 변경했습니다.
    limit: int = Query(2, ge=1, le=20, description="조회할 인기 게시글 개수 (최대 20개)"),
    db: Session = Depends(get_db)
):
    """
    조회수(views)가 가장 높은 게시글을 내림차순(DESC)으로 정렬하여 
    지정한 limit 개수만큼 반환합니다. (기본 2개 조회)
    """
    popular_posts = db.query(Post).order_by(Post.views.desc()).limit(limit).all()
    return popular_posts


@router.get("/{post_id}", response_model=PostDetailResponse)
def get_post_detail(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    
    # 조회 시 조회수를 1 증가시킨 후 저장 (GET 메서드로 일괄 처리)
    post.views += 1
    db.commit()
    db.refresh(post)
    return post


@router.post("/{post_id}/verify-password", response_model=PasswordVerifyResponse)
def verify_post_password(post_id: int, payload: PasswordVerifyRequest, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")

    return PasswordVerifyResponse(authorized=post.password == payload.password)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_post(post_data: PostCreate, db: Session = Depends(get_db)):
    new_post = Post(
        category=post_data.category,
        title=post_data.title,
        content=post_data.content,
        password=post_data.password,  # 평문 저장
        tags=post_data.tags
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return {"message": "게시글이 성공적으로 작성되었습니다.", "post_id": new_post.id}


@router.put("/{post_id}")
def update_post(post_id: int, update_data: PostUpdate, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    
    # 평문 패스워드 직접 대조 검증
    if post.password != update_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="비밀번호가 일치하지 않아 수정 권한이 없습니다."
        )
    
    post.title = update_data.title
    post.content = update_data.content
    post.tags = update_data.tags
    
    db.commit()
    return {"message": "게시글이 정상적으로 수정되었습니다."}


@router.delete("/{post_id}")
def delete_post(post_id: int, delete_data: PostDelete, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    
    # 평문 패스워드 직접 대조 검증
    if post.password != delete_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="비밀번호가 일치하지 않아 삭제 권한이 없습니다."
        )
    
    db.delete(post)
    db.commit()
    return {"message": "게시글이 성공적으로 삭제되었습니다."}