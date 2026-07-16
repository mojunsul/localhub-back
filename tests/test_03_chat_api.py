from unittest.mock import AsyncMock, patch

from app.chat.data_loader import DataLoadError
from app.chat.schemas import ChatResponse


def test_chat_health_endpoint(client_and_db):
    client, _ = client_and_db

    with patch("app.chat.router._service.health", return_value={"status": "ok"}):
        response = client.get("/api/chat/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_endpoint_returns_answer_from_service(client_and_db):
    client, _ = client_and_db

    fake_response = ChatResponse(
        answer="테스트 답변",
        results=[],
        mode="local-fallback",
        query_type="search",
    )

    with patch("app.chat.router._service.answer", new=AsyncMock(return_value=fake_response)) as mock_answer:
        response = client.post(
            "/api/chat",
            json={"message": "서울 여행", "history": []},
        )

    assert response.status_code == 200
    assert response.json()["answer"] == "테스트 답변"
    mock_answer.assert_awaited_once()


def test_chat_endpoint_returns_500_when_service_raises_data_error(client_and_db):
    client, _ = client_and_db

    with patch(
        "app.chat.router._service.answer",
        new=AsyncMock(side_effect=DataLoadError("데이터 로드 실패")),
    ):
        response = client.post(
            "/api/chat",
            json={"message": "서울 여행", "history": []},
        )

    assert response.status_code == 500
    assert response.json()["detail"] == "데이터 로드 실패"
