# 문화행사 패치 변경사항

## 추가 파일

- `app/chat/cultural_event_loader.py`
- `data/서울/서울시 문화행사 정보.json`
- `data/서울/CULTURAL_EVENT_SCHEMA.md`

## 수정 파일

- `app/chat/data_loader.py`
- `app/chat/search.py`
- `app/chat/schemas.py`
- `app/chat/service.py`
- `app/chat/prompt.py`
- `app/chat/smoke_test.py`
- `README_CHATBOT.md`
- `data/서울/SOURCE.md`

## 핵심 동작

- 전체 문화행사 유형 검색
- 날짜·시간·장소·가격 상세 답변
- 종료 행사 기본 제외
- 특정 과거 기간 요청 시 과거 행사 허용
- 날짜 오류 55건 제외
- 무료·유료, 자치구, 행사 유형, 특정 날짜 필터
