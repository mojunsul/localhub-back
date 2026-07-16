# LocalHub 챗봇 백엔드 — 모범음식점·문화행사 지원판

## 포함 기능

- 기존 관광지·문화시설·숙박·쇼핑 등 TourAPI 데이터 검색
- 서울 25개 자치구 모범음식점 지정 현황 검색
- 일반 음식점 질문을 모범음식점 데이터로 보완 검색
- 서울시 문화행사 전체 유형 검색
- 행사 날짜·시간·장소·요금·이용대상·문의처 조회
- 오늘·내일·이번 주·이번 주말·다음 주 일정 필터
- 진행 중·예정·종료 행사 구분
- 무료·유료 행사 필터
- 날짜가 잘못된 문화행사 55건 검색 제외
- 날짜 조건이 없는 일반 행사 검색에서 종료 행사 자동 제외
- API 키가 없거나 OpenAI 호출이 실패하면 로컬 답변으로 대체

## ZIP 적용 방법

프로젝트 최상위에서 압축을 풀어 기존 `backend` 폴더와 병합합니다.

```text
backend/
├─ app/chat/
├─ data/서울/
├─ README_CHATBOT.md
├─ requirements.txt
└─ .env.example
```

팀원이 만든 다음 공용 파일은 포함하지 않았습니다.

```text
app/main.py
app/database.py
app/models.py
app/routers/
```

기존 `app/main.py`에는 챗봇 라우터만 연결합니다.

```python
from app.chat.router import router as chat_router

app.include_router(chat_router)
```

## 설치 및 실행

```powershell
cd backend
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

챗봇 단독 확인:

```powershell
python -m uvicorn app.chat.dev_main:app --reload
```

- Swagger: `http://127.0.0.1:8000/docs`
- 상태 확인: `GET /api/chat/health`
- 챗봇 질문: `POST /api/chat`

## 데이터 확인

```powershell
python -m app.chat.smoke_test
```

현재 포함 데이터:

| 구분 | 건수 |
|---|---:|
| TourAPI 7개 유형 | 6,518 |
| 모범음식점 | 2,964 |
| 문화행사 원본 | 19,432 |
| 날짜 오류 제외 후 문화행사 | 19,377 |
| 챗봇 전체 로드 | 28,859 |

문화행사 원본은 삭제하거나 수정하지 않습니다. 날짜 형식이 잘못됐거나 종료일이 시작일보다 빠른 55건만 검색 인덱스에서 제외합니다.

## 문화행사 질문 예시

```text
오늘 문화행사 알려줘
이번 주말 무료 문화행사 알려줘
다음 주 마포구 클래식 공연 알려줘
2026년 8월 축제 알려줘
현재 진행 중인 전시 알려줘
지난 문화행사 알려줘
뮤라벨 콘서트 날짜 알려줘
뮤라벨 콘서트 시간과 장소 알려줘
뮤라벨 콘서트 가격 알려줘
뮤라벨 콘서트 무료인지 알려줘
```

## 문화행사 기본 필터 규칙

| 질문 | 검색 규칙 |
|---|---|
| 문화행사 알려줘 | 진행 중 또는 예정 행사만 |
| 오늘 행사 | 오늘과 행사 기간이 겹치는 항목 |
| 이번 주말 행사 | 토요일·일요일과 기간이 겹치는 항목 |
| 예정 행사 | 시작일이 오늘 이후인 항목 |
| 진행 중 행사 | 시작일 ≤ 오늘 ≤ 종료일 |
| 지난 행사 | 종료일이 오늘보다 이전인 항목 |
| 특정 과거 연도 | 종료된 행사도 해당 기간으로 검색 |
| 정확한 행사명 상세 질문 | 종료 여부와 관계없이 해당 행사 조회 |

## 문화행사 응답 필드

```json
{
  "category": "문화행사",
  "event_type": "클래식",
  "event_start_date": "2026-10-28",
  "event_end_date": "2026-10-28",
  "event_time": "(수) 19:30",
  "event_place": "마포아트센터 플레이맥",
  "use_fee": "전석 20,000원",
  "is_free": "유료",
  "target_audience": "8세이상 관람가능",
  "inquiry": "02-3274-8600",
  "event_status": "upcoming"
}
```

## 주의 사항

- 종료된 행사는 원본에서 삭제하지 않고 검색 단계에서만 숨깁니다.
- 특정 행사명을 물으면 종료된 행사도 상세 정보를 확인할 수 있습니다.
- `is_free`가 `유료`이지만 `use_fee`가 비어 있으면 정확한 금액은 안내하지 않습니다.
- 행사 데이터에 없는 평점·인기도·실시간 혼잡도는 생성하지 않습니다.
- 문화행사 JSON에 원본 데이터셋 라이선스가 포함되어 있지 않으므로 최종 제출 전에 실제 취득 페이지의 라이선스와 취득일을 기록해야 합니다.
