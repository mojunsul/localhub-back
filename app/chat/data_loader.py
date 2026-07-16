from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .config import get_settings
from .cultural_event_loader import (
    CULTURAL_EVENT_CATEGORY,
    CulturalEventLoadError,
    clear_cultural_event_cache,
    get_cultural_event_stats,
    load_cultural_events,
)
from .model_restaurant_loader import (
    MODEL_RESTAURANT_CATEGORY,
    ModelRestaurantLoadError,
    load_model_restaurants,
)
from .theme_tag_loader import (
    THEME_TAG_SOURCE,
    load_place_theme_tags,
    merge_place_theme_tags,
)


SOURCE_NAME = "한국관광공사 TourAPI 4.0"
SOURCE_URL = "https://www.data.go.kr/data/15101578/openapi.do"
SOURCE_LICENSE = "공공누리 제3유형"

# 일반 음식점과 모범음식점은 별도 데이터이므로 각각 상태를 표시한다.
EXPECTED_CATEGORIES = {
    "관광지",
    "레포츠",
    "문화시설",
    "쇼핑",
    "숙박",
    "여행코스",
    "음식점",
    MODEL_RESTAURANT_CATEGORY,
    "축제공연행사",
    CULTURAL_EVENT_CATEGORY,
}


class DataLoadError(RuntimeError):
    """서울 JSON 데이터를 불러오지 못했을 때 발생하는 오류."""


def get_seoul_data_dir() -> Path:
    return get_settings().seoul_data_dir


def _safe_float(value: object) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _join_address(addr1: object, addr2: object) -> str:
    parts = [
        str(part).strip()
        for part in (addr1, addr2)
        if str(part or "").strip()
    ]
    return " ".join(parts)


def _normalize_item(
    item: Dict[str, object],
    category: str,
) -> Dict[str, object]:
    """
    TourAPI 데이터를 검색용 공통 형식으로 읽기만 한다.
    원본 JSON 파일의 값은 수정하지 않는다.
    """
    return {
        "id": str(item.get("contentid", "")).strip(),
        "restaurant_key": "",
        "category": category.strip(),
        "title": str(item.get("title", "")).strip(),
        "address": _join_address(
            item.get("addr1", ""),
            item.get("addr2", ""),
        ),
        "jibun_address": "",
        "tel": str(item.get("tel", "")).strip(),
        "image": str(item.get("firstimage", "")).strip(),
        "longitude": _safe_float(item.get("mapx")),
        "latitude": _safe_float(item.get("mapy")),
        "content_type_id": str(item.get("contenttypeid", "")).strip(),
        "modified_at": str(item.get("modifiedtime", "")).strip(),
        "district": "",
        "district_dong": "",
        "main_food": "",
        "business_type": "",
        "designation_year": "",
        "designation_date": "",
        "designation_number": "",
        "permit_number": "",
        "business_area": None,
        "tags": [],
        "source_type": "official",
        "source": SOURCE_NAME,
        "source_url": SOURCE_URL,
        "license": SOURCE_LICENSE,
        "source_file": "",
    }


@lru_cache(maxsize=4)
def _load_cached(data_dir_text: str) -> Tuple[Dict[str, object], ...]:
    data_dir = Path(data_dir_text)

    if not data_dir.exists():
        raise DataLoadError(
            f"서울 데이터 폴더를 찾을 수 없습니다: {data_dir}\n"
            "backend/data/서울 경로를 확인하세요."
        )

    tour_files = sorted(data_dir.glob("서울_*.json"))
    model_files = sorted(
        data_dir.glob("서울시 *구 모범음식점 지정 현황.json")
    )
    cultural_event_files = sorted(
        data_dir.glob("서울시*문화행사*정보*.json")
    )

    if not tour_files and not model_files and not cultural_event_files:
        raise DataLoadError(
            f"서울 지역 JSON 파일을 찾을 수 없습니다: {data_dir}"
        )

    places: List[Dict[str, object]] = []
    errors: List[str] = []
    theme_tag_index = load_place_theme_tags(data_dir)

    for file_path in tour_files:
        try:
            with file_path.open("r", encoding="utf-8-sig") as file:
                payload = json.load(file)

            if not isinstance(payload, dict):
                raise ValueError("파일 최상위 값이 JSON 객체가 아닙니다.")

            category = str(
                payload.get("contentType")
                or file_path.stem.replace("서울_", "")
            ).strip()

            items = payload.get("items", [])
            if not isinstance(items, list):
                raise ValueError("'items' 값이 배열이 아닙니다.")

            for item in items:
                if not isinstance(item, dict):
                    continue

                normalized = _normalize_item(item, category)
                normalized["source_file"] = file_path.name
                normalized = merge_place_theme_tags(
                    normalized,
                    theme_tag_index,
                )
                if normalized["title"]:
                    places.append(normalized)

        except (OSError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"{file_path.name}: {exc}")

    try:
        places.extend(load_model_restaurants(data_dir))
    except ModelRestaurantLoadError as exc:
        errors.append(str(exc))

    try:
        places.extend(load_cultural_events(data_dir))
    except CulturalEventLoadError as exc:
        errors.append(str(exc))

    if errors:
        joined = "\n- ".join(errors)
        raise DataLoadError(
            f"일부 데이터 파일을 읽지 못했습니다.\n- {joined}"
        )

    if not places:
        raise DataLoadError("서울 데이터 항목이 0건입니다.")

    return tuple(places)


def load_seoul_places(
    data_dir: Optional[Path] = None,
) -> List[Dict[str, object]]:
    target = (data_dir or get_seoul_data_dir()).resolve()
    return list(_load_cached(str(target)))


def clear_data_cache() -> None:
    _load_cached.cache_clear()
    clear_cultural_event_cache()


def get_data_stats(
    data_dir: Optional[Path] = None,
) -> Dict[str, object]:
    target = (data_dir or get_seoul_data_dir()).resolve()
    places = load_seoul_places(target)
    categories: Dict[str, int] = {}

    for place in places:
        category = str(place.get("category", "기타"))
        categories[category] = categories.get(category, 0) + 1

    available = set(categories)
    from datetime import datetime
    from zoneinfo import ZoneInfo

    today = datetime.now(ZoneInfo("Asia/Seoul")).date()
    cultural_stats = get_cultural_event_stats(target, today)

    return {
        "data_dir": str(target),
        "total": len(places),
        "categories": dict(sorted(categories.items())),
        "missing_categories": sorted(EXPECTED_CATEGORIES - available),
        "model_restaurant_files": len(
            list(target.glob("서울시 *구 모범음식점 지정 현황.json"))
        ),
        "curated_theme_places": sum(
            1
            for place in places
            if str(place.get("tag_source", "")) == THEME_TAG_SOURCE
        ),
        **cultural_stats,
    }
