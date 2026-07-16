import pytest

from app.models import Post


def test_list_posts_returns_latest_posts_with_pagination(client_and_db):
    client, db = client_and_db

    db.add_all(
        [
            Post(
                category="맛집",
                title="첫 번째 글",
                content="내용1",
                password="1234",
                tags="태그1",
                views=10,
            ),
            Post(
                category="여행",
                title="두 번째 글",
                content="내용2",
                password="5678",
                tags="태그2",
                views=3,
            ),
        ]
    )
    db.commit()

    response = client.get("/api/posts?page=1&size=1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["total_count"] == 2
    assert payload["meta"]["size"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["title"] == "두 번째 글"


def test_list_posts_filters_by_title_and_tag(client_and_db):
    client, db = client_and_db

    db.add_all(
        [
            Post(category="맛집", title="강남 맛집", content="좋아요", password="pw", tags="강남"),
            Post(category="여행", title="서울 여행", content="재밌어요", password="pw", tags="서울"),
        ]
    )
    db.commit()

    response = client.get("/api/posts?title=맛집")
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["total_count"] == 1
    assert payload["items"][0]["title"] == "강남 맛집"

    response = client.get("/api/posts?tag=서울")
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["total_count"] == 1
    assert payload["items"][0]["title"] == "서울 여행"


def test_list_posts_filters_by_category(client_and_db):
    client, db = client_and_db

    db.add_all(
        [
            Post(category="맛집", title="강남 맛집", content="좋아요", password="pw", tags="강남"),
            Post(category="여행", title="서울 여행", content="재밌어요", password="pw", tags="서울"),
        ]
    )
    db.commit()

    response = client.get("/api/posts?category=맛집")

    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["total_count"] == 1
    assert payload["items"][0]["category"] == "맛집"
    assert payload["items"][0]["title"] == "강남 맛집"


def test_popular_posts_returns_highest_views_first(client_and_db):
    client, db = client_and_db

    db.add_all(
        [
            Post(category="정보", title="조회수 낮음", content="내용", password="pw", views=2),
            Post(category="정보", title="조회수 높음", content="내용", password="pw", views=99),
        ]
    )
    db.commit()

    response = client.get("/api/posts/popular?limit=2")

    assert response.status_code == 200
    payload = response.json()
    assert [post["title"] for post in payload] == ["조회수 높음", "조회수 낮음"]


def test_get_post_detail_increments_views(client_and_db):
    client, db = client_and_db

    post = Post(category="잡담", title="상세 조회 테스트", content="내용", password="pw", views=0)
    db.add(post)
    db.commit()
    db.refresh(post)

    response = client.get(f"/api/posts/{post.id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "상세 조회 테스트"
    assert payload["views"] == 1


def test_get_post_detail_returns_404_for_missing_post(client_and_db):
    client, _ = client_and_db

    response = client.get("/api/posts/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "게시글을 찾을 수 없습니다."


def test_verify_password_returns_true_for_correct_password(client_and_db):
    client, db = client_and_db

    post = Post(category="잡담", title="권한 확인", content="내용", password="pw")
    db.add(post)
    db.commit()
    db.refresh(post)

    response = client.post(
        f"/api/posts/{post.id}/verify-password",
        json={"password": "pw"},
    )

    assert response.status_code == 200
    assert response.json()["authorized"] is True


def test_verify_password_returns_false_for_wrong_password(client_and_db):
    client, db = client_and_db

    post = Post(category="잡담", title="권한 확인", content="내용", password="pw")
    db.add(post)
    db.commit()
    db.refresh(post)

    response = client.post(
        f"/api/posts/{post.id}/verify-password",
        json={"password": "wrong"},
    )

    assert response.status_code == 200
    assert response.json()["authorized"] is False


def test_create_post_returns_created_status(client_and_db):
    client, _ = client_and_db

    response = client.post(
        "/api/posts",
        json={
            "category": "공지",
            "title": "새 글",
            "content": "내용",
            "password": "pw",
            "tags": "공지",
        },
    )

    assert response.status_code == 201
    assert response.json()["message"] == "게시글이 성공적으로 작성되었습니다."


def test_create_post_returns_422_for_missing_required_fields(client_and_db):
    client, _ = client_and_db

    response = client.post(
        "/api/posts",
        json={
            "category": "공지",
            "content": "내용",
        },
    )

    assert response.status_code == 422


def test_update_post_returns_404_for_missing_post(client_and_db):
    client, _ = client_and_db

    response = client.put(
        "/api/posts/999999",
        json={
            "title": "수정 후",
            "content": "새 내용",
            "password": "pw",
            "tags": "수정",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "게시글을 찾을 수 없습니다."


def test_delete_post_returns_404_for_missing_post(client_and_db):
    client, _ = client_and_db

    response = client.request(
        "DELETE",
        "/api/posts/999999",
        json={"password": "pw"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "게시글을 찾을 수 없습니다."


def test_list_posts_returns_empty_result_for_no_match(client_and_db):
    client, _ = client_and_db

    response = client.get("/api/posts?title=없는검색어")

    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["total_count"] == 0
    assert payload["items"] == []


def test_update_post_succeeds_with_correct_password(client_and_db):
    client, db = client_and_db

    post = Post(category="잡담", title="수정 전", content="내용", password="pw")
    db.add(post)
    db.commit()
    db.refresh(post)

    response = client.put(
        f"/api/posts/{post.id}",
        json={
            "title": "수정 후",
            "content": "새 내용",
            "password": "pw",
            "tags": "수정",
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "게시글이 정상적으로 수정되었습니다."


def test_update_post_fails_with_wrong_password(client_and_db):
    client, db = client_and_db

    post = Post(category="잡담", title="수정 전", content="내용", password="pw")
    db.add(post)
    db.commit()
    db.refresh(post)

    response = client.put(
        f"/api/posts/{post.id}",
        json={
            "title": "수정 후",
            "content": "새 내용",
            "password": "wrong",
            "tags": "수정",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "비밀번호가 일치하지 않아 수정 권한이 없습니다."


def test_delete_post_succeeds_with_correct_password(client_and_db):
    client, db = client_and_db

    post = Post(category="잡담", title="삭제 대상", content="내용", password="pw")
    db.add(post)
    db.commit()
    db.refresh(post)

    response = client.request(
        "DELETE",
        f"/api/posts/{post.id}",
        json={"password": "pw"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "게시글이 성공적으로 삭제되었습니다."


def test_delete_post_fails_with_wrong_password(client_and_db):
    client, db = client_and_db

    post = Post(category="잡담", title="삭제 대상", content="내용", password="pw")
    db.add(post)
    db.commit()
    db.refresh(post)

    response = client.request(
        "DELETE",
        f"/api/posts/{post.id}",
        json={"password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "비밀번호가 일치하지 않아 삭제 권한이 없습니다."
