from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Sequence

from sqlalchemy import or_

from app.database import SessionLocal
from app.models import Post


TOKEN_PATTERN = re.compile(r"[가-힣A-Za-z0-9]+")
POST_SEARCH_STOPWORDS = {
    "게시글",
    "게시물",
    "게시판",
    "커뮤니티",
    "사용자",
    "작성글",
    "관련",
    "글",
    "후기",
    "검색",
    "검색해줘",
    "검색해주세요",
    "찾아줘",
    "찾아주세요",
    "보여줘",
    "보여주세요",
    "알려줘",
    "알려주세요",
    "해줘",
    "해주세요",
    "좀",
}
KOREAN_PARTICLES: Sequence[str] = (
    "에서는",
    "에서",
    "으로",
    "에게",
    "한테",
    "까지",
    "부터",
    "처럼",
    "보다",
    "하고",
    "와",
    "과",
    "은",
    "는",
    "이",
    "가",
    "을",
    "를",
    "에",
    "의",
    "도",
    "만",
    "로",
)


def _strip_particle(token: str) -> str:
    for particle in KOREAN_PARTICLES:
        if token.endswith(particle) and len(token) - len(particle) >= 2:
            return token[: -len(particle)]
    return token


def extract_post_keywords(question: str) -> List[str]:
    """게시글 검색 명령 표현을 제외하고 실제 검색어만 추출한다."""
    keywords: List[str] = []

    for raw_token in TOKEN_PATTERN.findall(question):
        token = _strip_particle(raw_token.strip())
        if len(token) < 2:
            continue
        if token in POST_SEARCH_STOPWORDS:
            continue
        if token.endswith(("해줘", "해주세요", "알려줘", "찾아줘", "보여줘")):
            continue
        if token not in keywords:
            keywords.append(token)

    return keywords


def _post_score(post: Post, keywords: Sequence[str]) -> int:
    title = (post.title or "").lower()
    content = (post.content or "").lower()
    tags = (post.tags or "").lower()

    score = 0
    for keyword in keywords:
        needle = keyword.lower()
        if needle in title:
            score += 5
        if needle in tags:
            score += 3
        if needle in content:
            score += 1
    return score


def _created_at_sort_value(value: Any) -> float:
    if isinstance(value, datetime):
        try:
            return value.timestamp()
        except (OSError, ValueError):
            return 0.0
    return 0.0


def search_posts_for_chat(
    question: str,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    LocalHub 게시판의 제목·본문·태그를 검색한다.

    비밀번호는 조회 결과에 포함하지 않으며, 챗봇에 필요한 공개 필드만 반환한다.
    검색어가 없으면 최신 게시글을 반환한다.
    """
    safe_limit = max(1, min(int(limit), 20))
    keywords = extract_post_keywords(question)
    db = SessionLocal()

    try:
        query = db.query(Post)

        if keywords:
            conditions = []
            for keyword in keywords:
                pattern = f"%{keyword}%"
                conditions.extend(
                    (
                        Post.title.ilike(pattern),
                        Post.content.ilike(pattern),
                        Post.tags.ilike(pattern),
                    )
                )
            query = query.filter(or_(*conditions))

        # Python 점수 정렬을 위해 후보를 조금 넉넉히 가져온다.
        candidates = (
            query.order_by(Post.created_at.desc(), Post.id.desc())
            .limit(max(safe_limit * 20, 100))
            .all()
        )

        if keywords:
            candidates.sort(
                key=lambda post: (
                    -_post_score(post, keywords),
                    -_created_at_sort_value(post.created_at),
                    -int(post.id or 0),
                )
            )

        results: List[Dict[str, Any]] = []
        for post in candidates[:safe_limit]:
            # password는 의도적으로 접근하거나 반환하지 않는다.
            results.append(
                {
                    "id": post.id,
                    "title": post.title,
                    "content": post.content,
                    "tags": post.tags,
                    "created_at": post.created_at,
                    "view_count": post.views,
                }
            )

        return results
    finally:
        db.close()
