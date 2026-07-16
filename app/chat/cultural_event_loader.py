from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse


CULTURAL_EVENT_CATEGORY = "문화행사"
CULTURAL_EVENT_SOURCE = "서울문화포털 서울시 문화행사 정보"
CULTURAL_EVENT_FILE_PATTERNS = (
    "서울시 문화행사 정보.json",
    "서울시*문화행사*정보*.json",
)

DATE_RANGE_PATTERN = re.compile(
    r"^\s*(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})\s*$"
)


class CulturalEventLoadError(RuntimeError):
    """서울시 문화행사 JSON을 읽지 못했을 때 발생한다."""


def _optional_text(value: object) -> str:
    return str(value or "").strip()


def _safe_float(value: object) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_date_range(value: object) -> Optional[Tuple[date, date]]:
    text = _optional_text(value)
    matched = DATE_RANGE_PATTERN.fullmatch(text)
    if not matched:
        return None

    try:
        start = datetime.strptime(matched.group(1), "%Y-%m-%d").date()
        end = datetime.strptime(matched.group(2), "%Y-%m-%d").date()
    except ValueError:
        return None

    if end < start:
        return None
    return start, end


def event_status(
    event: Dict[str, object],
    today: date,
) -> Optional[str]:
    try:
        start = date.fromisoformat(str(event.get("event_start_date", "")))
        end = date.fromisoformat(str(event.get("event_end_date", "")))
    except ValueError:
        return None

    if end < today:
        return "ended"
    if start > today:
        return "upcoming"
    return "ongoing"


def _event_id(row: Dict[str, Any]) -> str:
    detail_url = _optional_text(row.get("hmpg_addr"))
    if detail_url:
        try:
            cultcode = parse_qs(urlparse(detail_url).query).get("cultcode", [])
            if cultcode and cultcode[0]:
                return str(cultcode[0])
        except ValueError:
            pass

    raw = "|".join(
        (
            _optional_text(row.get("title")),
            _optional_text(row.get("date")),
            _optional_text(row.get("place")),
        )
    )
    return "culture-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def normalize_cultural_event(
    row: Dict[str, Any],
    source_file: str,
) -> Optional[Dict[str, object]]:
    parsed = parse_date_range(row.get("date"))
    if parsed is None:
        return None

    start, end = parsed
    title = _optional_text(row.get("title"))
    if not title:
        return None

    event_type = _optional_text(row.get("codename"))
    event_theme = _optional_text(row.get("themecode"))
    district = _optional_text(row.get("guname"))
    event_place = _optional_text(row.get("place"))
    free_or_paid = _optional_text(row.get("is_free"))
    use_fee = _optional_text(row.get("use_fee"))
    if not use_fee and free_or_paid == "무료":
        use_fee = "무료"

    detail_url = _optional_text(row.get("hmpg_addr"))
    homepage_url = _optional_text(row.get("org_link"))

    tags = [
        value
        for value in (
            CULTURAL_EVENT_CATEGORY,
            event_type,
            event_theme,
            district,
            free_or_paid,
            _optional_text(row.get("org_name")),
            str(start.year),
            f"{start.month}월",
        )
        if value
    ]

    return {
        "id": _event_id(row),
        "restaurant_key": "",
        "category": CULTURAL_EVENT_CATEGORY,
        "title": title,
        # 기존 프론트의 장소 카드와 호환되도록 행사 장소를 address에도 넣는다.
        "address": event_place,
        "jibun_address": "",
        "tel": _optional_text(row.get("inquiry")),
        "image": _optional_text(row.get("main_img")),
        "longitude": _safe_float(row.get("lot")),
        "latitude": _safe_float(row.get("lat")),
        "content_type_id": "seoul-cultural-event",
        "modified_at": _optional_text(row.get("rgstdate")),
        "district": district,
        "district_dong": "",
        "main_food": "",
        "business_type": "",
        "designation_year": "",
        "designation_date": "",
        "designation_number": "",
        "permit_number": "",
        "business_area": None,
        "event_type": event_type,
        "event_theme": event_theme,
        "event_start_date": start.isoformat(),
        "event_end_date": end.isoformat(),
        "event_date_text": _optional_text(row.get("date")),
        "event_time": _optional_text(row.get("pro_time")),
        "event_place": event_place,
        "use_fee": use_fee,
        "is_free": free_or_paid,
        "target_audience": _optional_text(row.get("use_trgt")),
        "inquiry": _optional_text(row.get("inquiry")),
        "organizer": _optional_text(row.get("org_name")),
        "performer": _optional_text(row.get("player")),
        "program": _optional_text(row.get("program")),
        "extra_description": _optional_text(row.get("etc_desc")),
        "homepage_url": homepage_url,
        "detail_url": detail_url,
        "registration_date": _optional_text(row.get("rgstdate")),
        "ticket_type": _optional_text(row.get("ticket")),
        "tags": tags,
        "source_type": "official",
        "source": CULTURAL_EVENT_SOURCE,
        # 개별 행사 상세 페이지를 출처 링크로 사용한다.
        "source_url": detail_url or homepage_url,
        # 제공된 파일에 라이선스 필드가 없어 임의로 작성하지 않는다.
        "license": None,
        "source_file": source_file,
    }


def find_cultural_event_files(data_dir: Path) -> List[Path]:
    found: Dict[str, Path] = {}
    for pattern in CULTURAL_EVENT_FILE_PATTERNS:
        for path in data_dir.glob(pattern):
            found[str(path.resolve())] = path
    return sorted(found.values(), key=lambda path: path.name)


@lru_cache(maxsize=8)
def _load_file_cached(
    path_text: str,
) -> Tuple[Tuple[Dict[str, object], ...], Dict[str, int]]:
    path = Path(path_text)
    try:
        with path.open("r", encoding="utf-8-sig") as file:
            payload = json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        raise CulturalEventLoadError(f"{path.name}: {exc}") from exc

    if not isinstance(payload, dict):
        raise CulturalEventLoadError(
            f"{path.name}: 파일 최상위 값이 JSON 객체가 아닙니다."
        )

    rows = payload.get("DATA", [])
    if not isinstance(rows, list):
        raise CulturalEventLoadError(
            f"{path.name}: 'DATA' 값이 배열이 아닙니다."
        )

    events: List[Dict[str, object]] = []
    invalid_dates = 0
    empty_titles = 0

    for row in rows:
        if not isinstance(row, dict):
            continue
        normalized = normalize_cultural_event(row, path.name)
        if normalized is None:
            if not _optional_text(row.get("title")):
                empty_titles += 1
            else:
                invalid_dates += 1
            continue
        events.append(normalized)

    stats = {
        "raw_total": len(rows),
        "loaded": len(events),
        "invalid_dates": invalid_dates,
        "empty_titles": empty_titles,
    }
    return tuple(events), stats


def load_cultural_events(data_dir: Path) -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []
    for path in find_cultural_event_files(data_dir):
        events, _ = _load_file_cached(str(path.resolve()))
        results.extend(events)
    return results


def get_cultural_event_stats(
    data_dir: Path,
    today: date,
) -> Dict[str, int]:
    raw_total = 0
    loaded = 0
    invalid_dates = 0
    empty_titles = 0
    ongoing = 0
    upcoming = 0
    ended = 0

    for path in find_cultural_event_files(data_dir):
        events, stats = _load_file_cached(str(path.resolve()))
        raw_total += stats["raw_total"]
        loaded += stats["loaded"]
        invalid_dates += stats["invalid_dates"]
        empty_titles += stats["empty_titles"]

        for event in events:
            status = event_status(event, today)
            if status == "ongoing":
                ongoing += 1
            elif status == "upcoming":
                upcoming += 1
            elif status == "ended":
                ended += 1

    return {
        "cultural_event_files": len(find_cultural_event_files(data_dir)),
        "cultural_event_raw_total": raw_total,
        "cultural_event_loaded": loaded,
        "cultural_event_invalid_dates": invalid_dates,
        "cultural_event_empty_titles": empty_titles,
        "cultural_event_ongoing": ongoing,
        "cultural_event_upcoming": upcoming,
        "cultural_event_ended": ended,
    }


def clear_cultural_event_cache() -> None:
    _load_file_cached.cache_clear()
