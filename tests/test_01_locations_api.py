def test_root_endpoint(client_and_db):
    client, _ = client_and_db

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "status": "running",
        "service": "LocalHub API Server",
    }


def test_list_locations_returns_paginated_results(client_and_db):
    client, db = client_and_db

    from app.models import Location

    db.add_all(
        [
            Location(
                category_id="C1",
                title="테스트 관광지",
                addr1="서울시 강남구",
                tel="010-1234-5678",
            ),
            Location(
                category_id="C2",
                title="다른 관광지",
                addr1="서울시 마포구",
                tel="010-1111-2222",
            ),
        ]
    )
    db.commit()

    response = client.get("/api/locations?page=1&size=1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["total_count"] == 2
    assert payload["meta"]["page"] == 1
    assert payload["meta"]["size"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["title"] == "테스트 관광지"


def test_list_locations_filters_by_keyword(client_and_db):
    client, db = client_and_db

    from app.models import Location

    db.add_all(
        [
            Location(category_id="C1", title="남산타워", addr1="서울시 용산구"),
            Location(category_id="C1", title="경복궁", addr1="서울시 종로구"),
        ]
    )
    db.commit()

    response = client.get("/api/locations?keyword=용산")

    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["total_count"] == 1
    assert payload["items"][0]["title"] == "남산타워"


def test_list_locations_filters_by_category_id(client_and_db):
    client, db = client_and_db

    from app.models import Location

    db.add_all(
        [
            Location(category_id="C1", title="남산타워", addr1="서울시 용산구"),
            Location(category_id="C2", title="경복궁", addr1="서울시 종로구"),
        ]
    )
    db.commit()

    response = client.get("/api/locations?category_id=C1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["total_count"] == 1
    assert payload["items"][0]["title"] == "남산타워"


def test_list_locations_returns_empty_result_for_no_match(client_and_db):
    client, _ = client_and_db

    response = client.get("/api/locations?keyword=없는키워드")

    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["total_count"] == 0
    assert payload["items"] == []
