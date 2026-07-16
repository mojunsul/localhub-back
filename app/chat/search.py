from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from zoneinfo import ZoneInfo

from .cultural_event_loader import (
    CULTURAL_EVENT_CATEGORY,
    event_status,
)
from .data_loader import load_seoul_places
from .model_restaurant_loader import MODEL_RESTAURANT_CATEGORY


CATEGORY_ALIASES = {
    MODEL_RESTAURANT_CATEGORY: (
        "모범음식점",
        "모범 음식점",
        "모범식당",
        "모범 식당",
    ),
    CULTURAL_EVENT_CATEGORY: (
        "문화행사",
        "문화 행사",
        "공연",
        "행사",
        "축제",
        "페스티벌",
        "전시",
        "콘서트",
        "클래식",
        "연극",
        "뮤지컬",
        "오페라",
        "무용",
        "국악",
        "영화",
        "독주회",
        "독창회",
        "교육 행사",
        "체험 행사",
    ),
    "관광지": (
        "관광지",
        "명소",
        "볼거리",
        "가볼만한곳",
        "가볼 만한 곳",
    ),
    "문화시설": (
        "문화시설",
        "문화공간",
    ),
    # 풍부한 일정 정보가 있는 서울시 문화행사 데이터를 우선 사용한다.
    # 기존 TourAPI 축제공연행사는 정확한 행사명 조회 때만 함께 검색될 수 있다.
    "축제공연행사": (
        "관광공사 축제",
        "TourAPI 축제",
    ),
    "여행코스": (
        "여행코스",
        "여행 코스",
        "코스",
        "동선",
    ),
    "레포츠": (
        "레포츠",
        "운동",
        "스포츠",
    ),
    "숙박": (
        "숙박",
        "숙소",
        "호텔",
        "게스트하우스",
        "펜션",
    ),
    "쇼핑": (
        "쇼핑",
        "시장",
        "백화점",
        "아울렛",
        "상점",
        "매장",
    ),
    "음식점": (
        "음식점",
        "맛집",
        "식당",
        "카페",
        "먹을 곳",
    ),
}

DETAIL_CATEGORY_MAP = {
    "박물관": "문화시설",
    "미술관": "문화시설",
    "갤러리": "문화시설",
    "전시관": "문화시설",
    "공연장": "문화시설",
    "도서관": "문화시설",
    "성당": "관광지",
    "사찰": "관광지",
    "궁궐": "관광지",
    "시장": "쇼핑",
    "백화점": "쇼핑",
    "호텔": "숙박",
    "게스트하우스": "숙박",
    "카페": "음식점",
}

EVENT_DETAIL_ALIASES = {
    "교육/체험": ("교육", "체험"),
    "전시/미술": ("전시", "미술", "미술전"),
    "클래식": ("클래식",),
    "콘서트": ("콘서트",),
    "기타": ("기타 행사",),
    "축제": ("축제", "페스티벌"),
    "연극": ("연극",),
    "국악": ("국악",),
    "뮤지컬/오페라": ("뮤지컬", "오페라"),
    "독주/독창회": ("독주", "독주회", "독창", "독창회"),
    "무용": ("무용", "댄스"),
    "영화": ("영화", "상영"),
}

SEOUL_DISTRICTS = (
    "강남구", "강동구", "강북구", "강서구", "관악구",
    "광진구", "구로구", "금천구", "노원구", "도봉구",
    "동대문구", "동작구", "마포구", "서대문구", "서초구",
    "성동구", "성북구", "송파구", "양천구", "영등포구",
    "용산구", "은평구", "종로구", "중구", "중랑구",
)

LOOKUP_WORDS = (
    "위치",
    "주소",
    "어디",
    "어딨어",
    "어디야",
    "어디서",
    "찾아가는 법",
    "전화번호",
    "연락처",
    "행사시간",
    "공연시간",
    "몇 시",
    "몇시",
    "입장료",
    "관람료",
    "이용요금",
    "가격이 얼마",
    "언제 열려",
    "언제 해",
)

RECOMMEND_WORDS = (
    "추천",
    "가볼 만한",
    "가볼만한",
    "골라줘",
    "여러 곳",
)

POST_WORDS = (
    "게시글",
    "게시물",
    "후기",
    "커뮤니티",
    "사용자 글",
)

GENERAL_UNAVAILABLE_DETAIL_WORDS = (
    "운영시간", "영업시간", "개장시간", "입장료", "가격", "요금",
    "휴무일", "예약", "주차 가능", "혼잡도", "실시간", "평점", "리뷰 점수",
)

CULTURAL_EVENT_UNAVAILABLE_DETAIL_WORDS = (
    "평점", "리뷰 점수", "혼잡도", "실시간 관람객", "주차 가능 여부",
)

EVENT_FREE_WORDS = ("무료", "공짜", "무료 행사", "무료 공연")
EVENT_PAID_WORDS = ("유료", "유료 행사", "유료 공연")
EVENT_ONGOING_WORDS = ("진행 중", "진행중", "현재 하는", "지금 하는", "열리고 있는")
EVENT_UPCOMING_WORDS = ("예정", "다가오는", "앞으로", "곧 하는", "개최 예정")
EVENT_ENDED_WORDS = ("지난", "종료된", "끝난", "예전에", "과거")
EVENT_STATUS_STOPWORDS = {
    "중인",
    "진행중",
    "진행중인",
    "진행하는",
    "진행되는",
    "예정된",
    "예정인",
    "개최예정",
    "개최될",
    "열리고",
    "열리는",
    "열릴",
    "곧",
}
STOPWORDS = {
    "서울", "서울시", "추천", "추천해줘", "추천해주세요", "알려줘", "알려주세요",
    "찾아줘", "찾아주세요", "어디", "어디야", "어딨어", "어디서", "있는", "있어", "있나요",
    "곳", "장소", "관련", "정보", "가볼", "만한", "근처", "좀", "해줘", "주세요",
    "현재", "등록된", "보여줘", "보여주세요", "위치", "주소", "전화번호", "연락처",
    "년도", "연도", "지정", "지정된", "시간", "행사시간", "공연시간", "날짜", "일정",
    "기간", "언제", "가격", "요금", "입장료", "관람료", "이용요금", "대상", "문의",
    "무료", "유료", "무료야", "유료야", "무료인지", "유료인지", "무료인가", "유료인가", "공짜야", "공짜인지", "오늘", "내일", "모레", "이번주", "이번", "주말", "다음주", "다음",
    "진행", "예정", "다가오는", "앞으로", "끝난", "종료된", "지난",
}

TOKEN_PATTERN = re.compile(r"[가-힣A-Za-z0-9]+")
NORMALIZE_PATTERN = re.compile(r"[^가-힣A-Za-z0-9]+")
YEAR_PATTERN = re.compile(r"\b(20\d{2})년?\b")
KOREAN_DATE_PATTERN = re.compile(
    r"(?:(20\d{2})년\s*)?(\d{1,2})월(?:\s*(\d{1,2})일)?"
)
ISO_DATE_PATTERN = re.compile(r"\b(20\d{2})-(\d{2})-(\d{2})\b")

KOREAN_PARTICLES = (
    "에서는", "에서", "으로", "에게", "한테", "까지", "부터", "처럼", "보다", "하고",
    "와", "과", "은", "는", "이", "가", "을", "를", "에", "의", "도", "만", "로",
)


@dataclass(frozen=True)
class QueryAnalysis:
    question: str
    query_type: str
    category: Optional[str]
    locations: Tuple[str, ...]
    detail_keywords: Tuple[str, ...]
    keywords: Tuple[str, ...]
    limitation_code: Optional[str]
    event_date_mode: Optional[str] = None
    event_period_start: Optional[str] = None
    event_period_end: Optional[str] = None
    event_date_explicit: bool = False
    event_price_filter: Optional[str] = None


@dataclass(frozen=True)
class SearchOutcome:
    analysis: QueryAnalysis
    results: List[Dict[str, object]]


def seoul_today() -> date:
    return datetime.now(ZoneInfo("Asia/Seoul")).date()


def normalize_text(text: str) -> str:
    return NORMALIZE_PATTERN.sub("", text).lower()


def _contains_any(question: str, words: Sequence[str]) -> bool:
    compact = normalize_text(question)
    return any(normalize_text(word) in compact for word in words)


def _strip_particle(token: str) -> str:
    for particle in KOREAN_PARTICLES:
        if token.endswith(particle) and len(token) - len(particle) >= 2:
            return token[:-len(particle)]
    return token


def detect_query_type(question: str) -> str:
    if _contains_any(question, POST_WORDS):
        return "post"
    if _contains_any(question, RECOMMEND_WORDS):
        return "recommend"
    if _contains_any(question, LOOKUP_WORDS):
        return "lookup"
    return "search"


def detect_category(question: str) -> Optional[str]:
    compact = normalize_text(question)

    for alias in CATEGORY_ALIASES[MODEL_RESTAURANT_CATEGORY]:
        if normalize_text(alias) in compact:
            return MODEL_RESTAURANT_CATEGORY

    # 행사 관련 표현은 기존 TourAPI 축제공연행사보다 상세 일정 데이터인 문화행사를 우선한다.
    for alias in CATEGORY_ALIASES[CULTURAL_EVENT_CATEGORY]:
        if normalize_text(alias) in compact:
            return CULTURAL_EVENT_CATEGORY

    for detail, category in DETAIL_CATEGORY_MAP.items():
        if normalize_text(detail) in compact:
            return category

    for category, aliases in CATEGORY_ALIASES.items():
        if category in {MODEL_RESTAURANT_CATEGORY, CULTURAL_EVENT_CATEGORY}:
            continue
        for alias in aliases:
            if normalize_text(alias) in compact:
                return category

    return None


def extract_detail_keywords(
    question: str,
    category: Optional[str],
) -> List[str]:
    compact = normalize_text(question)

    if category == CULTURAL_EVENT_CATEGORY:
        details: List[str] = []
        for canonical, aliases in EVENT_DETAIL_ALIASES.items():
            if any(normalize_text(alias) in compact for alias in aliases):
                if canonical not in details:
                    details.append(canonical)
        return details

    return [
        detail
        for detail in DETAIL_CATEGORY_MAP
        if normalize_text(detail) in compact
    ]


def extract_locations(question: str) -> List[str]:
    locations: List[str] = []

    for district in SEOUL_DISTRICTS:
        if district in question:
            locations.append(district)

    for raw_token in TOKEN_PATTERN.findall(question):
        token = _strip_particle(raw_token.strip())
        if (
            len(token) >= 3
            and token not in locations
            and token not in {"서울", "서울시"}
            and token.endswith(("동", "가"))
        ):
            locations.append(token)

    return locations


def _broad_alias_words() -> set[str]:
    words: set[str] = set()
    for aliases in CATEGORY_ALIASES.values():
        for alias in aliases:
            words.update(TOKEN_PATTERN.findall(alias))
    for aliases in EVENT_DETAIL_ALIASES.values():
        for alias in aliases:
            words.update(TOKEN_PATTERN.findall(alias))
    return words


BROAD_CATEGORY_WORDS = _broad_alias_words()


def extract_keywords(
    question: str,
    detail_keywords: Sequence[str],
    category: Optional[str],
) -> List[str]:
    keywords: List[str] = []

    for raw_token in TOKEN_PATTERN.findall(question):
        token = _strip_particle(raw_token.strip())
        year_match = re.fullmatch(r"(20\d{2})년", token)
        if year_match:
            if category == CULTURAL_EVENT_CATEGORY:
                continue
            token = year_match.group(1)

        if (
            category == CULTURAL_EVENT_CATEGORY
            and re.fullmatch(r"\d{1,2}(?:월|일)", token)
        ):
            continue

        if len(token) < 2:
            continue
        if category == CULTURAL_EVENT_CATEGORY and token.startswith(("무료", "유료", "공짜")):
            continue
        if token in STOPWORDS:
            continue
        if (
            category == CULTURAL_EVENT_CATEGORY
            and token in EVENT_STATUS_STOPWORDS
        ):
            continue
        if token in BROAD_CATEGORY_WORDS:
            continue
        if token in SEOUL_DISTRICTS:
            continue
        if token in detail_keywords:
            continue
        if token.endswith(("해주세요", "해줘", "알려줘", "찾아줘")):
            continue
        if token not in keywords:
            keywords.append(token)

    return keywords


def _month_period(year: int, month: int) -> Optional[Tuple[date, date]]:
    try:
        last_day = calendar.monthrange(year, month)[1]
        return date(year, month, 1), date(year, month, last_day)
    except ValueError:
        return None


def _weekend_period(today: date) -> Tuple[date, date]:
    weekday = today.weekday()
    if weekday == 6:  # 일요일이면 오늘 하루를 이번 주말로 본다.
        return today, today
    saturday = today + timedelta(days=max(0, 5 - weekday))
    return saturday, saturday + timedelta(days=1)


def detect_event_period(
    question: str,
    today: date,
) -> Tuple[Optional[str], Optional[date], Optional[date], bool]:
    compact = normalize_text(question)

    iso_match = ISO_DATE_PATTERN.search(question)
    if iso_match:
        try:
            target = date(
                int(iso_match.group(1)),
                int(iso_match.group(2)),
                int(iso_match.group(3)),
            )
            return "specific-date", target, target, True
        except ValueError:
            pass

    korean_match = KOREAN_DATE_PATTERN.search(question)
    if korean_match:
        year = int(korean_match.group(1) or today.year)
        month = int(korean_match.group(2))
        day_text = korean_match.group(3)
        try:
            if day_text:
                target = date(year, month, int(day_text))
                return "specific-date", target, target, True
            period = _month_period(year, month)
            if period:
                return "specific-month", period[0], period[1], True
        except ValueError:
            pass

    year_match = YEAR_PATTERN.search(question)
    if year_match:
        year = int(year_match.group(1))
        return "specific-year", date(year, 1, 1), date(year, 12, 31), True

    if "오늘" in compact:
        return "today", today, today, True
    if "내일" in compact:
        target = today + timedelta(days=1)
        return "tomorrow", target, target, True
    if "모레" in compact:
        target = today + timedelta(days=2)
        return "day-after-tomorrow", target, target, True
    if "이번주말" in compact or "주말" in compact:
        start, end = _weekend_period(today)
        return "this-weekend", start, end, True
    if "다음주" in compact:
        next_monday = today + timedelta(days=(7 - today.weekday()))
        return "next-week", next_monday, next_monday + timedelta(days=6), True
    if "이번주" in compact:
        sunday = today + timedelta(days=(6 - today.weekday()))
        return "this-week", today, sunday, True
    if _contains_any(question, EVENT_ONGOING_WORDS):
        return "ongoing", today, today, True
    if _contains_any(question, EVENT_UPCOMING_WORDS):
        return "upcoming", today + timedelta(days=1), None, True
    if _contains_any(question, EVENT_ENDED_WORDS):
        return "ended", None, today - timedelta(days=1), True

    return None, None, None, False


def detect_event_price_filter(question: str) -> Optional[str]:
    compact = normalize_text(question)
    # "무료인지", "유료야?"는 조건 검색이 아니라 해당 행사의 요금을 묻는 표현이다.
    if re.search(r"(?:무료|유료|공짜)(?:인지|인가|이야|야|인가요)", compact):
        return None
    if _contains_any(question, EVENT_FREE_WORDS):
        return "free"
    if _contains_any(question, EVENT_PAID_WORDS):
        return "paid"
    return None


def detect_limitation(
    question: str,
    category: Optional[str],
) -> Optional[str]:
    if category == CULTURAL_EVENT_CATEGORY:
        if _contains_any(question, CULTURAL_EVENT_UNAVAILABLE_DETAIL_WORDS):
            return "detail_field_missing"
        return None

    if category == "축제공연행사" and _contains_any(
        question,
        ("오늘", "내일", "주말", "언제", "일정", "기간", "날짜"),
    ):
        return "festival_schedule_missing"

    if _contains_any(question, GENERAL_UNAVAILABLE_DETAIL_WORDS):
        return "detail_field_missing"

    return None


def analyze_question(
    question: str,
    today: Optional[date] = None,
) -> QueryAnalysis:
    current = today or seoul_today()
    category = detect_category(question)
    details = extract_detail_keywords(question, category)
    date_mode, period_start, period_end, date_explicit = detect_event_period(
        question,
        current,
    )

    return QueryAnalysis(
        question=question,
        query_type=detect_query_type(question),
        category=category,
        locations=tuple(extract_locations(question)),
        detail_keywords=tuple(details),
        keywords=tuple(extract_keywords(question, details, category)),
        limitation_code=detect_limitation(question, category),
        event_date_mode=date_mode,
        event_period_start=period_start.isoformat() if period_start else None,
        event_period_end=period_end.isoformat() if period_end else None,
        event_date_explicit=date_explicit,
        event_price_filter=detect_event_price_filter(question),
    )


def result_limit_for(analysis: QueryAnalysis) -> int:
    if analysis.query_type == "lookup":
        return 1 if analysis.keywords else (5 if analysis.category == CULTURAL_EVENT_CATEGORY else 3)
    if analysis.query_type == "recommend":
        return 5
    if analysis.query_type == "post":
        return 5
    if analysis.category == CULTURAL_EVENT_CATEGORY:
        return 5
    return 3


def _searchable_text(place: Dict[str, object]) -> str:
    values = [
        place.get("title"),
        place.get("address"),
        place.get("jibun_address"),
        place.get("district"),
        place.get("district_dong"),
        place.get("main_food"),
        place.get("business_type"),
        place.get("designation_year"),
        place.get("designation_date"),
        place.get("event_type"),
        place.get("event_theme"),
        place.get("event_time"),
        place.get("event_place"),
        place.get("use_fee"),
        place.get("is_free"),
        place.get("target_audience"),
        place.get("organizer"),
        place.get("performer"),
        place.get("program"),
        place.get("extra_description"),
        place.get("event_start_date"),
        place.get("event_end_date"),
    ]
    tags = place.get("tags", [])
    if isinstance(tags, (list, tuple, set)):
        values.extend(tags)
    return " ".join(str(value).lower() for value in values if value)


def _matches_category_and_location(
    place: Dict[str, object],
    category: Optional[str],
    locations: Sequence[str],
) -> bool:
    place_category = str(place.get("category", ""))
    search_text = _searchable_text(place)

    if category and place_category != category:
        return False

    for location in locations:
        if location.lower() not in search_text:
            return False

    return True


def _event_detail_matches(
    canonical: str,
    place: Dict[str, object],
) -> bool:
    event_type = normalize_text(
        str(place.get("event_type", ""))
    )
    title = normalize_text(
        str(place.get("title", ""))
    )

    if canonical == "전시/미술":
        return event_type == normalize_text("전시/미술")

    if canonical == "클래식":
        return event_type == normalize_text("클래식")

    if canonical == "축제":
        return (
            event_type.startswith(normalize_text("축제"))
            or normalize_text("축제") in title
        )

    aliases = EVENT_DETAIL_ALIASES.get(
        canonical,
        (canonical,),
    )

    return any(
        normalize_text(alias) in event_type
        or normalize_text(alias) in title
        for alias in aliases
    )


def _event_overlaps(
    place: Dict[str, object],
    start: Optional[date],
    end: Optional[date],
) -> bool:
    try:
        event_start = date.fromisoformat(str(place.get("event_start_date", "")))
        event_end = date.fromisoformat(str(place.get("event_end_date", "")))
    except ValueError:
        return False

    if start is not None and event_end < start:
        return False
    if end is not None and event_start > end:
        return False
    return True


def _matches_event_filters(
    place: Dict[str, object],
    analysis: QueryAnalysis,
    today: date,
    apply_default_active_filter: bool,
) -> bool:
    if str(place.get("category", "")) != CULTURAL_EVENT_CATEGORY:
        return True

    status = event_status(place, today)
    if status is None:
        return False

    if analysis.event_price_filter == "free" and str(place.get("is_free", "")) != "무료":
        return False
    if analysis.event_price_filter == "paid" and str(place.get("is_free", "")) != "유료":
        return False

    mode = analysis.event_date_mode
    if mode == "ongoing":
        return status == "ongoing"
    if mode == "upcoming":
        return status == "upcoming"
    if mode == "ended":
        return status == "ended"

    if analysis.event_date_explicit:
        start = (
            date.fromisoformat(analysis.event_period_start)
            if analysis.event_period_start
            else None
        )
        end = (
            date.fromisoformat(analysis.event_period_end)
            if analysis.event_period_end
            else None
        )
        return _event_overlaps(place, start, end)

    # 행사명으로 정확히 조회할 때는 과거 행사도 확인할 수 있게 한다.
    if not apply_default_active_filter:
        return True

    # 날짜 조건이 없는 일반 문화행사 질문은 종료되지 않은 행사만 노출한다.
    return status in {"ongoing", "upcoming"}


def _exact_title_matches(
    question: str,
    places: Sequence[Dict[str, object]],
    analysis: QueryAnalysis,
    today: date,
) -> List[Dict[str, object]]:
    question_normalized = normalize_text(question)
    matches: List[Dict[str, object]] = []

    for place in places:
        # 사용자가 명시한 카테고리가 있으면 정확한 제목 검색에서도 지킨다.
        # 예: "야경 명소"가 과거 문화행사의 제목 키워드와 겹치더라도
        # 관광지 질문에 문화행사를 섞지 않는다.
        if not _matches_category_and_location(
            place,
            analysis.category,
            analysis.locations,
        ):
            continue

        title = str(place.get("title", "")).strip()
        title_normalized = normalize_text(title)
        if len(title_normalized) < 3:
            continue

        # 전체 제목이 질문에 포함되거나, 제목의 의미 있는 일부가 질문에 포함된 경우.
        direct_match = title_normalized in question_normalized
        partial_match = False
        if (
            str(place.get("category", "")) == CULTURAL_EVENT_CATEGORY
            and analysis.keywords
        ):
            title_compact = normalize_text(title)
            partial_match = all(
                normalize_text(keyword) in title_compact
                for keyword in analysis.keywords
            )

        if not direct_match and not partial_match:
            continue

        if (
            str(place.get("category", "")) == CULTURAL_EVENT_CATEGORY
            and any(
                not _event_detail_matches(detail, place)
                for detail in analysis.detail_keywords
            )
        ):
            continue

        # 전체 행사명이 질문에 그대로 포함된 직접 조회는 종료된 행사도 허용한다.
        # 단순 키워드 부분 일치라면 일반 검색과 동일하게 종료 행사를 제외한다.
        allow_ended_exact_event = (
            str(place.get("category", "")) == CULTURAL_EVENT_CATEGORY
            and direct_match
        )
        if not _matches_event_filters(
            place,
            analysis,
            today,
            apply_default_active_filter=not allow_ended_exact_event,
        ):
            continue

        matches.append(place)

    matches.sort(key=lambda place: _result_sort_key(place, analysis, today))
    return _deduplicate(matches)


def _score_place(
    place: Dict[str, object],
    analysis: QueryAnalysis,
    today: date,
) -> int:
    title = str(place.get("title", "")).lower()
    address = str(place.get("address", "")).lower()
    search_text = _searchable_text(place)
    place_category = str(place.get("category", ""))

    if not _matches_category_and_location(place, analysis.category, analysis.locations):
        return -1

    if not _matches_event_filters(
        place,
        analysis,
        today,
        apply_default_active_filter=(analysis.category == CULTURAL_EVENT_CATEGORY),
    ):
        return -1

    for detail in analysis.detail_keywords:
        if place_category == CULTURAL_EVENT_CATEGORY:
            if not _event_detail_matches(detail, place):
                return -1
        elif detail.lower() not in title:
            return -1

    score = 0
    if analysis.category and place_category == analysis.category:
        score += 5

    for location in analysis.locations:
        location_lower = location.lower()
        if location_lower in address:
            score += 25
        elif location_lower in title:
            score += 15
        elif location_lower in search_text:
            score += 12

    for detail in analysis.detail_keywords:
        if place_category == CULTURAL_EVENT_CATEGORY and _event_detail_matches(detail, place):
            score += 40
        elif detail.lower() in title:
            score += 40

    for keyword in analysis.keywords:
        keyword_lower = keyword.lower()
        if keyword_lower == title:
            score += 120
        elif keyword_lower in title:
            score += 35
        elif keyword_lower in str(place.get("main_food", "")).lower():
            score += 25
        elif keyword_lower in str(place.get("business_type", "")).lower():
            score += 22
        elif keyword_lower in str(place.get("designation_year", "")).lower():
            score += 20
        elif keyword_lower in str(place.get("event_type", "")).lower():
            score += 28
        elif keyword_lower in str(place.get("event_theme", "")).lower():
            score += 20
        elif keyword_lower in str(place.get("event_place", "")).lower():
            score += 18
        elif keyword_lower in str(place.get("organizer", "")).lower():
            score += 15
        elif keyword_lower in address:
            score += 10
        elif keyword_lower in search_text:
            score += 8
        else:
            return -1

    if (
        not analysis.locations
        and not analysis.detail_keywords
        and not analysis.keywords
        and analysis.category
    ):
        score += 1

    if place_category == CULTURAL_EVENT_CATEGORY:
        status = event_status(place, today)
        if status == "ongoing":
            score += 8
        elif status == "upcoming":
            score += 4

    return score


def _designation_number(place: Dict[str, object]) -> int:
    value = str(place.get("designation_date", "") or "")
    digits = re.sub(r"\D", "", value)
    try:
        return int(digits) if digits else 0
    except ValueError:
        return 0


def _event_date_number(place: Dict[str, object], key: str) -> int:
    value = str(place.get(key, "") or "").replace("-", "")
    try:
        return int(value) if value.isdigit() else 99999999
    except ValueError:
        return 99999999


def _result_sort_key(
    place: Dict[str, object],
    analysis: QueryAnalysis,
    today: date,
) -> Tuple[object, ...]:
    if str(place.get("category", "")) == CULTURAL_EVENT_CATEGORY:
        status = event_status(place, today)
        if analysis.event_date_mode == "ended":
            return (
                0,
                -_event_date_number(place, "event_end_date"),
                str(place.get("title", "")),
            )
        status_order = {"ongoing": 0, "upcoming": 1, "ended": 2, None: 3}
        event_date_key = (
            _event_date_number(place, "event_end_date")
            if status == "ongoing"
            else _event_date_number(place, "event_start_date")
        )
        return (
            status_order.get(status, 3),
            event_date_key,
            str(place.get("title", "")),
        )

    return (
        0,
        -_designation_number(place),
        str(place.get("title", "")),
    )


def _deduplicate(places: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []
    seen: set[Tuple[str, str]] = set()

    for place in places:
        category = str(place.get("category", ""))
        if category == MODEL_RESTAURANT_CATEGORY:
            key_value = str(
                place.get("restaurant_key")
                or place.get("permit_number")
                or f"{place.get('title')}|{place.get('address')}"
            )
        elif category == CULTURAL_EVENT_CATEGORY:
            key_value = "|".join(
                (
                    str(place.get("title", "")),
                    str(place.get("event_start_date", "")),
                    str(place.get("event_end_date", "")),
                    str(place.get("event_place", "")),
                )
            )
        else:
            key_value = str(
                place.get("id", "")
                or f"{place.get('title')}|{place.get('address')}"
            )

        key = (category, key_value)
        if key in seen:
            continue
        seen.add(key)
        results.append(place)

    return results


def search_places(
    question: str,
    places: Optional[Iterable[Dict[str, object]]] = None,
    limit: Optional[int] = None,
    today: Optional[date] = None,
) -> SearchOutcome:
    source = list(places) if places is not None else load_seoul_places()
    current = today or seoul_today()
    analysis = analyze_question(question, today=current)

    if analysis.query_type == "post":
        return SearchOutcome(analysis=analysis, results=[])

    resolved_limit = limit if limit is not None else result_limit_for(analysis)
    if resolved_limit < 1:
        return SearchOutcome(analysis=analysis, results=[])

    # 상세 필드 제한 여부와 관계없이 먼저 정확한 제목을 찾아본다.
    exact_matches = _exact_title_matches(question, source, analysis, current)
    if exact_matches:
        return SearchOutcome(
            analysis=analysis,
            results=exact_matches[:1] if analysis.query_type == "lookup" else exact_matches[:resolved_limit],
        )

    scored: List[Tuple[int, Dict[str, object]]] = []
    for place in source:
        score = _score_place(place, analysis, current)
        if score > 0:
            scored.append((score, place))

    scored.sort(
        key=lambda item: (
            -item[0],
            *_result_sort_key(item[1], analysis, current),
        )
    )

    unique_places = _deduplicate([place for _, place in scored])
    return SearchOutcome(
        analysis=analysis,
        results=unique_places[:resolved_limit],
    )
