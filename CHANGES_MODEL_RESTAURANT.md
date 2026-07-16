# 모범음식점 지원 변경 파일

## 새 파일

- `app/chat/model_restaurant_loader.py`
- `data/서울/MODEL_RESTAURANT_SCHEMA.md`
- `data/서울/서울시 *구 모범음식점 지정 현황.json` 25개

## 수정 파일

- `app/chat/data_loader.py`
- `app/chat/search.py`
- `app/chat/schemas.py`
- `app/chat/service.py`
- `app/chat/prompt.py`
- `app/chat/openai_client.py`
- `app/chat/config.py`
- `app/chat/smoke_test.py`
- `.env.example`
- `README_CHATBOT.md`
- `data/서울/SOURCE.md`

## 건드리지 않은 팀 공용 파일

- `app/main.py`
- `app/database.py`
- `app/models.py`
- `app/routers/`

압축을 `backend`에 병합한 뒤 `python -m app.chat.smoke_test`로 확인합니다.
