from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


MODEL_RESTAURANT_GLOB = "서울시 *구 모범음식점 지정 현황.json"
MODEL_RESTAURANT_CATEGORY = "모범음식점"
MODEL_RESTAURANT_SOURCE = "서울시 자치구별 모범음식점 지정 현황"


class ModelRestaurantLoadError(RuntimeError):
    """모범음식점 지정 현황 JSON을 읽지 못했을 때 발생한다."""


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _safe_float(value: object) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def extract_district_from_filename(path: Path) -> str:
    """'서울시 성동구 모범음식점 지정 현황.json'에서 '성동구'를 얻는다."""
    match = re.search(r"서울시\s+(.+?구)\s+모범음식점", path.stem)
    return match.group(1).strip() if match else ""


def normalize_model_restaurant(
    row: Dict[str, Any],
    district: str,
    source_file: str,
) -> Dict[str, object]:
    """
    자치구별 모범음식점 원본을 챗봇 검색용 공통 구조로 변환한다.

    원본 JSON 파일은 변경하지 않으며, 검색 시 사용할 내부 값만 만든다.
    """
    title = _text(row.get("upso_nm"))
    road_address = _text(row.get("site_addr_rd"))
    jibun_address = _text(row.get("site_addr"))
    dong = _text(row.get("admdng_nm"))
    main_food = _text(row.get("main_edf"))
    business_type = _text(row.get("snt_uptae_nm"))
    designation_year = _text(row.get("asgn_yy"))
    designation_date = _text(row.get("asgn_ymd"))
    permit_number = _text(row.get("perm_nt_no"))
    designation_number = _text(row.get("asgn_sno"))
    tel = _text(row.get("upso_site_telno"))

    restaurant_key = permit_number or "|".join(
        value for value in (district, title, road_address or jibun_address) if value
    )
    record_id = ":".join(
        value for value in (restaurant_key, designation_date or designation_year) if value
    )

    tags = [
        value
        for value in (
            MODEL_RESTAURANT_CATEGORY,
            district,
            dong,
            business_type,
            main_food,
            designation_year,
        )
        if value
    ]

    return {
        "id": record_id or restaurant_key or title,
        "restaurant_key": restaurant_key or record_id or title,
        "category": MODEL_RESTAURANT_CATEGORY,
        "title": title,
        "address": road_address or jibun_address,
        "jibun_address": jibun_address,
        "tel": tel,
        "image": "",
        "longitude": None,
        "latitude": None,
        "content_type_id": "model_restaurant",
        "modified_at": designation_date,
        "district": district,
        "district_dong": dong,
        "main_food": main_food,
        "business_type": business_type,
        "designation_year": designation_year,
        "designation_date": designation_date,
        "designation_number": designation_number,
        "permit_number": permit_number,
        "business_area": _safe_float(row.get("trdp_area")),
        "tags": tags,
        "source_type": "official",
        "source": f"{MODEL_RESTAURANT_SOURCE} ({district})" if district else MODEL_RESTAURANT_SOURCE,
        # 업로드된 JSON에는 원본 페이지 URL과 라이선스 값이 포함되어 있지 않다.
        "source_url": "",
        "license": "",
        "source_file": source_file,
    }


def load_model_restaurants(data_dir: Path) -> List[Dict[str, object]]:
    files = sorted(data_dir.glob(MODEL_RESTAURANT_GLOB))
    results: List[Dict[str, object]] = []
    errors: List[str] = []

    for file_path in files:
        try:
            with file_path.open("r", encoding="utf-8-sig") as file:
                payload = json.load(file)

            if not isinstance(payload, dict):
                raise ValueError("파일 최상위 값이 JSON 객체가 아닙니다.")

            rows = payload.get("DATA", [])
            if not isinstance(rows, list):
                raise ValueError("'DATA' 값이 배열이 아닙니다.")

            district = extract_district_from_filename(file_path)
            if not district:
                raise ValueError("파일명에서 자치구를 확인할 수 없습니다.")

            for row in rows:
                if not isinstance(row, dict):
                    continue
                normalized = normalize_model_restaurant(
                    row=row,
                    district=district,
                    source_file=file_path.name,
                )
                if normalized["title"]:
                    results.append(normalized)

        except (OSError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"{file_path.name}: {exc}")

    if errors:
        joined = "\n- ".join(errors)
        raise ModelRestaurantLoadError(
            f"일부 모범음식점 파일을 읽지 못했습니다.\n- {joined}"
        )

    return results
