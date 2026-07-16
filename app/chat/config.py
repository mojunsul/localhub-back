from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[2]


def _load_env() -> None:
    """backend/.env를 읽되, python-dotenv가 없으면 OS 환경변수만 사용한다."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    load_dotenv(BACKEND_DIR / ".env")


_load_env()


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_model: str
    database_url: str
    seoul_data_dir: Path

    @property
    def openai_configured(self) -> bool:
        return bool(self.openai_api_key.strip())

    @property
    def database_configured(self) -> bool:
        return bool(self.database_url.strip())


def get_settings() -> Settings:
    data_dir_text = os.getenv("LOCALHUB_SEOUL_DATA_DIR", "").strip()
    data_dir = (
        Path(data_dir_text).expanduser().resolve()
        if data_dir_text
        else BACKEND_DIR / "data" / "서울"
    )

    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-5-mini").strip(),
        # 팀 DB 구조나 배포 환경에 따라 .env에서 변경한다.
        database_url=os.getenv("DATABASE_URL", "sqlite:///./backend.db").strip(),
        seoul_data_dir=data_dir,
    )
