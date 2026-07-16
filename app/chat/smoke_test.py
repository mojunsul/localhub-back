"""
OpenAI API 호출 없이 검색 품질과 데이터 방어 규칙을 확인한다.

backend 폴더에서:
    python -m app.chat.smoke_test
"""

from datetime import date

from .cultural_event_loader import CULTURAL_EVENT_CATEGORY, event_status
from .data_loader import get_data_stats, load_seoul_places
from .search import search_places


TEST_TODAY = date(2026, 7, 15)


def main() -> None:
    places = load_seoul_places()
    stats = get_data_stats()

    print("[데이터 로딩 성공]")
    print(f"전체 건수: {stats['total']}")
    print(f"카테고리: {stats['categories']}")
    print(f"누락 카테고리: {stats['missing_categories']}")
    print(f"모범음식점 파일 수: {stats['model_restaurant_files']}")
    print(f"문화행사 파일 수: {stats['cultural_event_files']}")
    print()

    assert stats["model_restaurant_files"] == 25
    assert stats["categories"].get("모범음식점") == 2964
    print("[성공] 25개 자치구 모범음식점 2,964건 로드")

    assert stats["cultural_event_files"] == 1
    assert stats["cultural_event_raw_total"] == 19432
    assert stats["cultural_event_loaded"] == 19377
    assert stats["cultural_event_invalid_dates"] == 55
    assert stats["categories"].get(CULTURAL_EVENT_CATEGORY) == 19377
    print("[성공] 문화행사 19,377건 로드, 날짜 오류 55건 제외")

    assert stats["curated_theme_places"] == 25
    print("[성공] 관광지 테마 태그 25곳 결합")

    lookup = search_places("서울숲 위치 알려줘", places=places)
    assert len(lookup.results) == 1
    assert lookup.results[0]["title"] == "서울숲"
    print("[성공] 특정 장소 조회 → 서울숲 1건")

    hotels = search_places("강남구 숙소 추천해줘", places=places)
    assert len(hotels.results) == 5
    assert all(
        result["category"] == "숙박" and "강남구" in result["address"]
        for result in hotels.results
    )
    print("[성공] 추천 질문 → 강남구 숙박 5건")

    model_restaurants = search_places(
        "성동구 모범음식점 알려줘",
        places=places,
    )
    assert len(model_restaurants.results) == 3
    assert all(
        result["category"] == "모범음식점"
        and result["district"] == "성동구"
        for result in model_restaurants.results
    )
    print("[성공] 성동구 모범음식점 목록 검색")

    event_detail = search_places(
        "뮤라벨 콘서트 시간과 장소, 가격 알려줘",
        places=places,
        today=TEST_TODAY,
    )
    assert len(event_detail.results) == 1
    event = event_detail.results[0]
    assert event["category"] == CULTURAL_EVENT_CATEGORY
    assert event["event_time"] == "(수) 19:30"
    assert event["event_place"] == "마포아트센터 플레이맥"
    assert event["use_fee"] == "전석 20,000원"
    print("[성공] 행사명 기반 시간·장소·가격 조회")

    today_events = search_places(
        "오늘 문화행사 알려줘",
        places=places,
        today=TEST_TODAY,
    )
    assert today_events.results
    assert all(
        result["event_start_date"] <= TEST_TODAY.isoformat()
        <= result["event_end_date"]
        for result in today_events.results
    )
    print("[성공] 오늘 날짜와 겹치는 문화행사 검색")

    weekend_free = search_places(
        "이번 주말 무료 문화행사 알려줘",
        places=places,
        today=TEST_TODAY,
    )
    assert weekend_free.results
    assert all(result["is_free"] == "무료" for result in weekend_free.results)
    assert all(
        result["event_start_date"] <= "2026-07-19"
        and result["event_end_date"] >= "2026-07-18"
        for result in weekend_free.results
    )
    print("[성공] 이번 주말 무료 문화행사 검색")

    august_festivals = search_places(
        "2026년 8월 축제 알려줘",
        places=places,
        today=TEST_TODAY,
    )
    assert august_festivals.results
    assert all(
        str(result["event_type"]).startswith("축제-")
        for result in august_festivals.results
    )
    assert all(
        result["event_start_date"] <= "2026-08-31"
        and result["event_end_date"] >= "2026-08-01"
        for result in august_festivals.results
    )
    print("[성공] 특정 월의 축제 일정 검색")

    active_events = search_places(
        "문화행사 알려줘",
        places=places,
        today=TEST_TODAY,
    )
    assert active_events.results
    assert all(
        event_status(result, TEST_TODAY) in {"ongoing", "upcoming"}
        for result in active_events.results
    )
    print("[성공] 일반 행사 검색에서 종료 행사 자동 제외")

    past_events = search_places(
        "지난 문화행사 알려줘",
        places=places,
        today=TEST_TODAY,
    )
    assert past_events.results
    assert all(
        event_status(result, TEST_TODAY) == "ended"
        for result in past_events.results
    )
    print("[성공] 과거 행사 요청 시 종료 행사 검색")

    assert all(
        result.get("source") == "한국관광공사 TourAPI 4.0"
        for result in lookup.results
    )
    print("[성공] TourAPI 공식 출처 메타데이터 포함")

    ongoing_exhibitions = search_places(
        "현재 진행 중인 전시",
        places=places,
        today=TEST_TODAY,
    )

    assert ongoing_exhibitions.results
    assert all(
        result["event_type"] == "전시/미술"
        for result in ongoing_exhibitions.results
    )
    assert all(
        event_status(result, TEST_TODAY) == "ongoing"
        for result in ongoing_exhibitions.results
    )

    print("[성공] 현재 진행 중인 전시 검색")

    upcoming_classics = search_places(
        "예정된 클래식 공연",
        places=places,
        today=TEST_TODAY,
    )

    assert upcoming_classics.results
    assert all(
        result["event_type"] == "클래식"
        for result in upcoming_classics.results
    )
    assert all(
        event_status(result, TEST_TODAY) == "upcoming"
        for result in upcoming_classics.results
    )

    print("[성공] 예정된 클래식 공연 검색")

    night_spots = search_places(
        "서울 야경 명소를 추천해줘",
        places=places,
        today=TEST_TODAY,
    )
    assert night_spots.results
    assert all(
        result.get("category") == "관광지"
        for result in night_spots.results
    )
    assert all(
        "야경" in result.get("tags", [])
        for result in night_spots.results
    )
    print("[성공] 야경 태그가 결합된 관광지만 검색")

    night_events = search_places(
        "야경 행사 알려줘",
        places=places,
        today=TEST_TODAY,
    )
    assert all(
        event_status(result, TEST_TODAY) in {"ongoing", "upcoming"}
        for result in night_events.results
    )
    print("[성공] 일반 야경 행사 검색에서 종료 행사 제외")
    
    print()
    print("모든 스모크 테스트를 통과했습니다.")


if __name__ == "__main__":
    main()
