from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Mapping


THEME_TAG_FILE_NAME = "place_theme_tags.json"
THEME_TAG_SOURCE = "LocalHub 팀 큐레이션"


def _normalize_key(value: object) -> str:
    """
    장소명 비교용 키를 만든다.

    원본 제목은 바꾸지 않고, 비교할 때만 유니코드와 공백을 정규화한다.
    """
    text = unicodedata.normalize("NFKC", str(value or ""))
    return "".join(text.lower().split())


def _clean_tags(value: object) -> List[str]:
    if not isinstance(value, list):
        return []

    cleaned: List[str] = []
    for tag in value:
        text = str(tag or "").strip()
        if text and text not in cleaned:
            cleaned.append(text)
    return cleaned


def load_place_theme_tags(
    seoul_data_dir: Path,
) -> Dict[str, Dict[str, List[str]]]:
    """
    backend/data/curation/place_theme_tags.json을 읽는다.

    지원 구조:
    {
      "by_title": {"서울숲": ["산책", "데이트"]},
      "by_id": {"12345": ["야경"]}
    }
    """
    tag_path = (
        seoul_data_dir.resolve().parent
        / "curation"
        / THEME_TAG_FILE_NAME
    )

    empty = {"by_title": {}, "by_id": {}}
    if not tag_path.exists():
        return empty

    try:
        payload = json.loads(tag_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[테마 태그] 파일을 읽지 못했습니다: {tag_path}: {exc}")
        return empty

    if not isinstance(payload, dict):
        print(f"[테마 태그] 최상위 값이 객체가 아닙니다: {tag_path}")
        return empty

    title_rows = payload.get("by_title", {})
    id_rows = payload.get("by_id", {})

    by_title: Dict[str, List[str]] = {}
    by_id: Dict[str, List[str]] = {}

    if isinstance(title_rows, dict):
        for title, tags in title_rows.items():
            key = _normalize_key(title)
            cleaned = _clean_tags(tags)
            if key and cleaned:
                by_title[key] = cleaned

    if isinstance(id_rows, dict):
        for content_id, tags in id_rows.items():
            key = str(content_id or "").strip()
            cleaned = _clean_tags(tags)
            if key and cleaned:
                by_id[key] = cleaned

    return {
        "by_title": by_title,
        "by_id": by_id,
    }


def merge_place_theme_tags(
    place: Mapping[str, Any],
    tag_index: Mapping[str, Mapping[str, List[str]]],
) -> Dict[str, Any]:
    """
    원본 장소 dict를 직접 수정하지 않고 태그가 결합된 새 dict를 반환한다.
    """
    result = dict(place)

    original_tags = result.get("tags", [])
    if not isinstance(original_tags, list):
        original_tags = []

    content_id = str(result.get("id", "") or "").strip()
    title_key = _normalize_key(result.get("title", ""))

    by_id = tag_index.get("by_id", {})
    by_title = tag_index.get("by_title", {})

    added_tags: List[str] = []
    if content_id and content_id in by_id:
        added_tags.extend(by_id[content_id])
    if title_key and title_key in by_title:
        added_tags.extend(by_title[title_key])

    merged: List[str] = []
    for tag in [*original_tags, *added_tags]:
        text = str(tag or "").strip()
        if text and text not in merged:
            merged.append(text)

    result["tags"] = merged

    if added_tags:
        # 검색·디버깅용 내부 메타데이터다.
        # 공식 TourAPI 출처 필드는 그대로 유지한다.
        result["tag_source"] = THEME_TAG_SOURCE

    return result
