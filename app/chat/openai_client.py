from __future__ import annotations

from .config import get_settings
from .prompt import SYSTEM_INSTRUCTIONS


class OpenAIClientUnavailable(RuntimeError):
    """OpenAI SDK 또는 API 키를 사용할 수 없을 때 발생한다."""


def is_openai_configured() -> bool:
    return get_settings().openai_configured


async def generate_openai_answer(model_input: str) -> str:
    settings = get_settings()

    if not settings.openai_api_key:
        raise OpenAIClientUnavailable(
            "OPENAI_API_KEY가 설정되지 않았습니다."
        )

    try:
        from openai import AsyncOpenAI
    except ImportError as exc:
        raise OpenAIClientUnavailable(
            "openai 패키지가 설치되지 않았습니다."
        ) from exc

    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        timeout=30.0,
        max_retries=1,
    )

    response = await client.responses.create(
        model=settings.openai_model,
        instructions=SYSTEM_INSTRUCTIONS,
        input=model_input,
        max_output_tokens=450,
        temperature=0.2,
        store=False,
    )

    answer = (response.output_text or "").strip()
    if not answer:
        raise OpenAIClientUnavailable(
            "OpenAI 응답 내용이 비어 있습니다."
        )

    return answer
