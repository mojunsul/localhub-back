# 서울시 문화행사 정보 스키마

## 원본 구조

```json
{
  "DESCRIPTION": {},
  "DATA": []
}
```

## 주요 필드

| 원본 필드 | 의미 | 챗봇 내부 필드 |
|---|---|---|
| `title` | 공연/행사명 | `title` |
| `codename` | 분류 | `event_type` |
| `date` | 행사 기간 | `event_start_date`, `event_end_date` |
| `pro_time` | 행사시간 | `event_time` |
| `place` | 장소 | `event_place`, `address` |
| `guname` | 자치구 | `district` |
| `use_fee` | 이용요금 | `use_fee` |
| `is_free` | 유무료 | `is_free` |
| `use_trgt` | 이용대상 | `target_audience` |
| `inquiry` | 문의 | `inquiry`, `tel` |
| `org_name` | 기관명 | `organizer` |
| `player` | 출연자정보 | `performer` |
| `program` | 프로그램소개 | `program` |
| `main_img` | 대표이미지 | `image` |
| `org_link` | 기관 홈페이지 | `homepage_url` |
| `hmpg_addr` | 서울문화포털 상세 URL | `detail_url`, `source_url` |
| `lat`, `lot` | 위도·경도 | `latitude`, `longitude` |

## 날짜 방어 규칙

- `date`는 `YYYY-MM-DD~YYYY-MM-DD` 형식만 허용합니다.
- 종료일이 시작일보다 빠르면 검색 인덱스에서 제외합니다.
- 원본 JSON은 수정하지 않습니다.
- 일반 행사 검색은 종료일이 오늘 이후인 행사만 보여줍니다.
- 과거 날짜·연도 또는 종료된 행사를 명시하면 과거 행사도 검색합니다.
