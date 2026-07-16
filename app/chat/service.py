from __future__ import annotations

import inspect
import logging
from pathlib import Path
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Union,
)

from .config import get_settings
from .cultural_event_loader import (
    CULTURAL_EVENT_CATEGORY,
    CULTURAL_EVENT_SOURCE,
    event_status,
)
from .data_loader import get_data_stats, load_seoul_places
from .model_restaurant_loader import (
    MODEL_RESTAURANT_CATEGORY,
    MODEL_RESTAURANT_SOURCE,
)
from .openai_client import generate_openai_answer, is_openai_configured
from .prompt import build_model_input
from .schemas import ChatRequest, ChatResponse, ChatResult
from .search import (
    QueryAnalysis,
    SearchOutcome,
    search_places,
    seoul_today,
)


logger = logging.getLogger(__name__)

PostRows = Sequence[Mapping[str, Any]]
PostSearchReturn = Union[PostRows, Awaitable[PostRows]]
PostSearcher = Callable[[str, int], PostSearchReturn]

ALLOWED_POST_KEYS = {
    "id",
    "post_id",
    "title",
    "content",
    "tags",
    "created_at",
    "updated_at",
    "view_count",
    "views",
}

GENERIC_FOOD_WORDS = (
    "음식점",
    "식당",
    "맛집",
    "먹을 곳",
    "한식",
    "중식",
    "중국식",
    "일식",
    "양식",
    "경양식",
    "분식",
    "뷔페",
    "한우",
    "삼겹살",
    "갈비",
    "국밥",
    "찌개",
)


class ChatService:
    def __init__(
        self,
        data_dir: Optional[Path] = None,
        post_searcher: Optional[PostSearcher] = None,
    ) -> None:
        self.data_dir = data_dir
        self.post_searcher = post_searcher
        self._places: Optional[List[Dict[str, object]]] = None

    def set_post_searcher(
        self,
        searcher: Optional[PostSearcher],
    ) -> None:
        self.post_searcher = searcher

    def _get_places(self) -> List[Dict[str, object]]:
        if self._places is None:
            self._places = load_seoul_places(self.data_dir)
        return self._places

    async def _search_posts(
        self,
        question: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        if self.post_searcher is None:
            return []

        result = self.post_searcher(question, limit)
        if inspect.isawaitable(result):
            result = await result

        normalized: List[Dict[str, Any]] = []
        for row in result or []:
            mapping = dict(row)
            clean = {
                key: mapping[key]
                for key in ALLOWED_POST_KEYS
                if key in mapping
            }
            if "content" in clean:
                clean["content"] = str(clean["content"])[:800]
            normalized.append(clean)

        return normalized[:limit]

    @staticmethod
    def _optional_text(place: Mapping[str, Any], key: str) -> Optional[str]:
        value = str(place.get(key, "") or "").strip()
        return value or None

    @classmethod
    def _place_to_result(cls, place: Mapping[str, Any]) -> ChatResult:
        tags = place.get("tags", [])
        if not isinstance(tags, list):
            tags = []

        status = None
        if str(place.get("category", "")) == CULTURAL_EVENT_CATEGORY:
            status = event_status(dict(place), seoul_today())

        return ChatResult(
            type="place",
            id=str(place.get("id", "")),
            title=str(place.get("title", "")),
            category=cls._optional_text(place, "category"),
            address=cls._optional_text(place, "address"),
            tel=cls._optional_text(place, "tel"),
            image=cls._optional_text(place, "image"),
            tags=[str(tag) for tag in tags],
            district=cls._optional_text(place, "district"),
            district_dong=cls._optional_text(place, "district_dong"),
            jibun_address=cls._optional_text(place, "jibun_address"),
            main_food=cls._optional_text(place, "main_food"),
            business_type=cls._optional_text(place, "business_type"),
            designation_year=cls._optional_text(place, "designation_year"),
            designation_date=cls._optional_text(place, "designation_date"),
            designation_number=cls._optional_text(place, "designation_number"),
            permit_number=cls._optional_text(place, "permit_number"),
            event_type=cls._optional_text(place, "event_type"),
            event_theme=cls._optional_text(place, "event_theme"),
            event_start_date=cls._optional_text(place, "event_start_date"),
            event_end_date=cls._optional_text(place, "event_end_date"),
            event_date_text=cls._optional_text(place, "event_date_text"),
            event_time=cls._optional_text(place, "event_time"),
            event_place=cls._optional_text(place, "event_place"),
            use_fee=cls._optional_text(place, "use_fee"),
            is_free=cls._optional_text(place, "is_free"),
            target_audience=cls._optional_text(place, "target_audience"),
            inquiry=cls._optional_text(place, "inquiry"),
            organizer=cls._optional_text(place, "organizer"),
            performer=cls._optional_text(place, "performer"),
            program=cls._optional_text(place, "program"),
            homepage_url=cls._optional_text(place, "homepage_url"),
            detail_url=cls._optional_text(place, "detail_url"),
            event_status=status,
            source_type="official",
            source=str(place.get("source", "공식 서울 지역정보")),
            source_url=cls._optional_text(place, "source_url"),
            license=cls._optional_text(place, "license"),
            modified_at=cls._optional_text(place, "modified_at"),
        )

    @staticmethod
    def _post_to_result(post: Mapping[str, Any]) -> ChatResult:
        post_id = post.get("id", post.get("post_id", ""))
        tags = post.get("tags", [])

        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
        elif not isinstance(tags, list):
            tags = []

        content = " ".join(str(post.get("content", "") or "").split())
        preview = content[:160] + ("…" if len(content) > 160 else "")
        created_at = post.get("created_at")
        view_count = post.get("view_count", post.get("views"))

        return ChatResult(
            type="post",
            id=post_id,
            title=str(post.get("title", "제목 없는 게시글")),
            category="커뮤니티",
            tags=[str(tag) for tag in tags],
            content_preview=preview or None,
            created_at=str(created_at) if created_at is not None else None,
            view_count=int(view_count) if view_count is not None else None,
            source_type="community",
            source="LocalHub 사용자 작성 게시글",
        )

    @staticmethod
    def _limitation_response(
        analysis: QueryAnalysis,
        available_categories: set[str],
        search_results: Sequence[Mapping[str, Any]],
    ) -> Optional[ChatResponse]:
        # 문화행사 데이터에는 날짜·시간·장소·요금 필드가 있으므로
        # 기존 TourAPI의 상세정보 제한을 적용하지 않는다.
        if (
            analysis.category == CULTURAL_EVENT_CATEGORY
            or any(
                str(result.get("category", "")) == CULTURAL_EVENT_CATEGORY
                for result in search_results
            )
        ):
            if analysis.limitation_code != "detail_field_missing":
                return None
            return ChatResponse(
                answer=(
                    "현재 문화행사 데이터에는 요청하신 평점·실시간 혼잡도 같은 "
                    "정보가 포함되어 있지 않습니다. 날짜, 시간, 장소, 이용요금, "
                    "이용대상과 문의처는 제공된 범위에서 안내할 수 있습니다."
                ),
                results=[],
                mode="data-limited",
                query_type=analysis.query_type,
                notice="요청한 상세 필드가 문화행사 데이터에 없습니다.",
            )

        if analysis.limitation_code == "festival_schedule_missing":
            return ChatResponse(
                answer=(
                    "현재 선택된 관광공사 축제 데이터에는 행사 시작일과 종료일이 "
                    "포함되어 있지 않아 정확한 일정을 확인할 수 없습니다. "
                    "서울시 문화행사 데이터로 질문하면 일정 검색이 가능합니다."
                ),
                results=[],
                mode="data-limited",
                query_type=analysis.query_type,
                notice="선택된 데이터에 축제 날짜 필드가 없습니다.",
            )

        if analysis.limitation_code == "detail_field_missing":
            return ChatResponse(
                answer=(
                    "현재 제공된 공공데이터에는 요청하신 운영시간·가격·휴무일·"
                    "평점 등의 상세 정보가 포함되어 있지 않아 정확히 안내할 수 "
                    "없습니다. 장소명과 주소 정보는 검색할 수 있습니다."
                ),
                results=[],
                mode="data-limited",
                query_type=analysis.query_type,
                notice="요청한 상세 필드가 제공 데이터에 없습니다.",
            )

        if (
            not search_results
            and analysis.category
            and analysis.category not in available_categories
        ):
            category = analysis.category
            return ChatResponse(
                answer=(
                    f"현재 프로젝트의 서울 데이터 폴더에는 '{category}' "
                    "데이터 파일이 없어 해당 질문에 답할 수 없습니다. "
                    "관련 JSON 파일을 추가하면 자동으로 검색됩니다."
                ),
                results=[],
                mode="data-limited",
                query_type=analysis.query_type,
                notice=f"{category} 데이터 파일이 없습니다.",
            )

        return None

    @staticmethod
    def _source_line(places: Sequence[Mapping[str, Any]]) -> str:
        has_tourapi = any(
            str(place.get("source", "")).startswith("한국관광공사 TourAPI")
            for place in places
        )
        has_model_restaurant = any(
            str(place.get("category", "")) == MODEL_RESTAURANT_CATEGORY
            for place in places
        )
        has_cultural_event = any(
            str(place.get("category", "")) == CULTURAL_EVENT_CATEGORY
            for place in places
        )

        lines: List[str] = []
        if has_tourapi:
            lines.append("한국관광공사 TourAPI 4.0 (공공누리 제3유형)")
        if has_model_restaurant:
            lines.append(MODEL_RESTAURANT_SOURCE)
        if has_cultural_event:
            lines.append(CULTURAL_EVENT_SOURCE)

        if not lines:
            unique_sources = []
            for place in places:
                source = str(place.get("source", "")).strip()
                if source and source not in unique_sources:
                    unique_sources.append(source)
            lines.extend(unique_sources[:3])

        return "출처: " + ", ".join(lines) if lines else ""

    @staticmethod
    def _format_designation_date(value: object) -> str:
        text = str(value or "").strip()
        if len(text) == 8 and text.isdigit():
            return f"{text[:4]}-{text[4:6]}-{text[6:]}"
        return text

    @staticmethod
    def _format_event_period(place: Mapping[str, Any]) -> str:
        start = str(place.get("event_start_date", "") or "").strip()
        end = str(place.get("event_end_date", "") or "").strip()
        if start and end:
            return start if start == end else f"{start} ~ {end}"
        return start or end

    @staticmethod
    def _event_status_label(place: Mapping[str, Any]) -> str:
        status = event_status(dict(place), seoul_today())
        return {
            "ongoing": "진행 중",
            "upcoming": "예정",
            "ended": "종료",
        }.get(status, "")

    @staticmethod
    def _event_fee_text(place: Mapping[str, Any]) -> str:
        use_fee = str(place.get("use_fee", "") or "").strip()
        free_or_paid = str(place.get("is_free", "") or "").strip()
        if use_fee:
            return use_fee
        if free_or_paid == "무료":
            return "무료"
        if free_or_paid == "유료":
            return "유료(정확한 금액 정보 없음)"
        return "요금 정보 없음"

    @classmethod
    def _cultural_event_lookup_answer(
        cls,
        place: Mapping[str, Any],
    ) -> str:
        title = str(place.get("title", ""))
        lines = [title]

        status = cls._event_status_label(place)
        if status:
            lines.append(f"- 상태: {status}")

        period = cls._format_event_period(place)
        if period:
            lines.append(f"- 날짜: {period}")

        event_time = str(place.get("event_time", "") or "").strip()
        if event_time:
            lines.append(f"- 시간: {event_time}")

        event_place = str(place.get("event_place", "") or "").strip()
        district = str(place.get("district", "") or "").strip()
        if event_place:
            place_text = f"{district} {event_place}" if district else event_place
            lines.append(f"- 장소: {place_text}")

        lines.append(f"- 요금: {cls._event_fee_text(place)}")

        target = str(place.get("target_audience", "") or "").strip()
        if target:
            lines.append(f"- 이용대상: {target}")

        inquiry = str(place.get("inquiry", "") or "").strip()
        if inquiry:
            lines.append(f"- 문의: {inquiry}")

        return "\n".join(lines)

    @classmethod
    def _fallback_answer(
        cls,
        analysis: QueryAnalysis,
        places: Sequence[Mapping[str, Any]],
        posts: Sequence[Mapping[str, Any]],
    ) -> str:
        parts: List[str] = []

        if places:
            all_events = all(
                str(place.get("category", "")) == CULTURAL_EVENT_CATEGORY
                for place in places
            )

            if all_events and len(places) == 1:
                parts.append(cls._cultural_event_lookup_answer(places[0]))

            elif analysis.query_type == "lookup" and len(places) == 1:
                place = places[0]
                title = str(place.get("title", ""))
                address = str(place.get("address", ""))
                tel = str(place.get("tel", ""))
                main_food = str(place.get("main_food", ""))
                designation_date = cls._format_designation_date(
                    place.get("designation_date", "")
                )

                sentence = (
                    f"{title}의 주소는 {address}입니다."
                    if address
                    else f"{title}의 주소 정보는 제공 데이터에 없습니다."
                )
                if tel:
                    sentence += f" 전화번호는 {tel}입니다."
                if main_food:
                    sentence += f" 주된 음식은 {main_food}입니다."
                if designation_date:
                    sentence += f" 모범음식점 지정일자는 {designation_date}입니다."
                parts.append(sentence)

            else:
                lines: List[str] = []
                for index, place in enumerate(places, start=1):
                    title = str(place.get("title", ""))
                    address = str(place.get("address", ""))
                    category = str(place.get("category", ""))

                    if category == CULTURAL_EVENT_CATEGORY:
                        event_type = str(place.get("event_type", ""))
                        period = cls._format_event_period(place)
                        event_time = str(place.get("event_time", "") or "").strip()
                        event_place = str(place.get("event_place", "") or "").strip()
                        fee = cls._event_fee_text(place)

                        line = f"{index}. {title}"
                        if event_type:
                            line += f" ({event_type})"
                        details = [value for value in (period, event_time, event_place, fee) if value]
                        if details:
                            line += " — " + " — ".join(details)
                        lines.append(line)
                        continue

                    main_food = str(place.get("main_food", ""))
                    business_type = str(place.get("business_type", ""))
                    designation_year = str(place.get("designation_year", ""))

                    line = f"{index}. {title}"
                    if category:
                        line += f" ({category})"
                    details = [value for value in (business_type, main_food) if value]
                    if details:
                        line += " — " + " / ".join(details)
                    if address:
                        line += f" — {address}"
                    if designation_year:
                        line += f" — {designation_year}년 지정"
                    lines.append(line)

                if all_events:
                    mode_labels = {
                        "today": "오늘 열리는",
                        "tomorrow": "내일 열리는",
                        "day-after-tomorrow": "모레 열리는",
                        "this-week": "이번 주 열리는",
                        "this-weekend": "이번 주말 열리는",
                        "next-week": "다음 주 열리는",
                        "ongoing": "현재 진행 중인",
                        "upcoming": "앞으로 예정된",
                        "ended": "종료된",
                        "specific-date": "요청한 날짜에 열리는",
                        "specific-month": "요청한 달에 열리는",
                        "specific-year": "요청한 연도에 열리는",
                    }
                    condition = mode_labels.get(
                        analysis.event_date_mode,
                        "현재 진행 중이거나 예정된",
                    )
                    intro = (
                        f"서울시 문화행사 정보에서 {condition} 행사 "
                        f"{len(places)}건을 찾았습니다."
                    )
                elif analysis.query_type == "recommend":
                    intro = (
                        "평점이나 인기도 순위가 아니라, 입력한 지역·유형 "
                        f"조건에 맞춰 검색된 장소 {len(places)}곳입니다."
                    )
                elif analysis.category == MODEL_RESTAURANT_CATEGORY:
                    intro = (
                        "제공된 자치구별 모범음식점 지정 현황에서 조건에 맞는 "
                        f"업소 {len(places)}곳을 찾았습니다."
                    )
                else:
                    detail = (
                        f" '{', '.join(analysis.detail_keywords)}'"
                        if analysis.detail_keywords
                        else ""
                    )
                    intro = (
                        f"요청한 조건{detail}에 맞는 장소 "
                        f"{len(places)}곳을 찾았습니다."
                    )

                parts.append(intro + "\n" + "\n".join(lines))

            source_line = cls._source_line(places)
            if source_line:
                parts.append(source_line)

        if posts:
            post_lines: List[str] = []
            for index, post in enumerate(posts, start=1):
                title = str(post.get("title", "제목 없는 게시글"))
                content = " ".join(str(post.get("content", "") or "").split())
                preview = content[:120] + ("…" if len(content) > 120 else "")
                line = f"{index}. {title}"
                if preview:
                    line += f" — {preview}"
                post_lines.append(line)

            parts.append(
                f"관련 커뮤니티 게시글 {len(posts)}건을 찾았습니다.\n"
                + "\n".join(post_lines)
                + "\n주의: 사용자 작성 정보이므로 사실 여부를 별도로 확인해 주세요."
            )

        if not parts:
            if analysis.category == MODEL_RESTAURANT_CATEGORY:
                return (
                    "제공된 서울시 자치구별 모범음식점 지정 현황에서 "
                    "해당 조건과 일치하는 업소를 찾지 못했습니다. "
                    "자치구, 행정동, 음식 종류 또는 업소명을 포함해 다시 질문해 주세요."
                )
            if analysis.category == CULTURAL_EVENT_CATEGORY:
                return (
                    "해당 조건과 일치하는 문화행사를 찾지 못했습니다. "
                    "행사 유형, 자치구, 날짜 또는 행사명을 바꿔 검색해 주세요. "
                    "종료된 행사는 과거 날짜나 연도를 명시해야 검색됩니다."
                )
            return (
                "관련 정보를 찾지 못했습니다. 장소명, 서울 자치구 또는 "
                "관광지·문화시설·숙박 같은 유형을 포함해 다시 질문해 주세요."
            )

        return "\n\n".join(parts)

    @staticmethod
    def _is_general_food_query(
        question: str,
        analysis: QueryAnalysis,
    ) -> bool:
        compact = question.replace(" ", "").lower()
        if analysis.category == "음식점":
            return True
        return any(word.replace(" ", "") in compact for word in GENERIC_FOOD_WORDS)

    @staticmethod
    def _convert_to_model_restaurant_query(question: str) -> str:
        compact = question.replace(" ", "")
        if "모범음식점" in compact or "모범식당" in compact:
            return question

        converted = question
        for word in ("음식점", "식당", "맛집", "먹을 곳"):
            if word in converted:
                return converted.replace(word, "모범음식점", 1)
        return converted + " 모범음식점"

    @staticmethod
    def _combine_notices(*notices: Optional[str]) -> Optional[str]:
        values = [notice.strip() for notice in notices if notice and notice.strip()]
        return " ".join(values) if values else None

    async def answer(self, request: ChatRequest) -> ChatResponse:
        message = request.message.strip()
        places_source = self._get_places()

        available_categories = {
            str(place.get("category", ""))
            for place in places_source
        }

        outcome: SearchOutcome = search_places(
            question=message,
            places=places_source,
        )
        analysis = outcome.analysis
        food_search_notice: Optional[str] = None

        # 일반 음식점 파일이 없을 때 음식 관련 질문은 모범음식점 지정 현황으로 보완한다.
        should_use_model_restaurants = (
            not outcome.results
            and MODEL_RESTAURANT_CATEGORY in available_categories
            and self._is_general_food_query(message, analysis)
            and analysis.category != MODEL_RESTAURANT_CATEGORY
        )
        if should_use_model_restaurants:
            converted_question = self._convert_to_model_restaurant_query(message)
            converted_outcome = search_places(
                question=converted_question,
                places=places_source,
            )
            if converted_outcome.results:
                outcome = converted_outcome
                analysis = outcome.analysis
                food_search_notice = (
                    "일반 음식점 데이터가 없어 서울시 자치구별 "
                    "모범음식점 지정 현황을 기준으로 검색했습니다."
                )

        limited = self._limitation_response(
            analysis,
            available_categories,
            search_results=outcome.results,
        )
        if limited:
            return limited

        posts: List[Dict[str, Any]] = []
        if analysis.query_type == "post":
            posts = await self._search_posts(message, limit=5)

        places = outcome.results
        results: List[ChatResult] = [self._place_to_result(place) for place in places]
        results.extend(self._post_to_result(post) for post in posts)

        if not places and not posts:
            if analysis.query_type == "post" and self.post_searcher is None:
                return ChatResponse(
                    answer=(
                        "커뮤니티 게시글 검색 기능이 아직 DB 검색 함수와 "
                        "연결되지 않았습니다."
                    ),
                    results=[],
                    mode="data-limited",
                    query_type=analysis.query_type,
                    notice="게시글 검색 어댑터가 연결되지 않았습니다.",
                )

            return ChatResponse(
                answer=self._fallback_answer(analysis, places, posts),
                results=[],
                mode="no-result",
                query_type=analysis.query_type,
                notice=food_search_notice,
            )

        openai_failure_notice: Optional[str] = None
        if is_openai_configured():
            try:
                model_input = build_model_input(
                    message=message,
                    history=request.history,
                    analysis=analysis,
                    place_results=places,
                    post_results=posts,
                )
                answer = await generate_openai_answer(model_input)
                return ChatResponse(
                    answer=answer,
                    results=results,
                    mode="openai",
                    query_type=analysis.query_type,
                    notice=food_search_notice,
                )
            except Exception:
                logger.exception(
                    "OpenAI 답변 생성 실패. 로컬 응답으로 대체합니다."
                )
                openai_failure_notice = (
                    "OpenAI 호출에 실패해 검색 결과를 로컬 형식으로 표시했습니다."
                )
        else:
            openai_failure_notice = (
                "OPENAI_API_KEY가 없어 로컬 답변을 사용했습니다."
            )

        return ChatResponse(
            answer=self._fallback_answer(analysis, places, posts),
            results=results,
            mode="local-fallback",
            query_type=analysis.query_type,
            notice=self._combine_notices(
                food_search_notice,
                openai_failure_notice,
            ),
        )

    def health(self) -> Dict[str, Any]:
        stats = get_data_stats(self.data_dir)
        settings = get_settings()

        return {
            "status": "ok",
            "openai_configured": settings.openai_configured,
            "database_configured": settings.database_configured,
            "post_search_configured": self.post_searcher is not None,
            **stats,
        }
