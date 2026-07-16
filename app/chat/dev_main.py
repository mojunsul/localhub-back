"""
챗봇만 단독으로 실행하는 개발용 FastAPI 앱.

backend 폴더에서:
    uvicorn app.chat.dev_main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .router import router


app = FastAPI(title="LocalHub Chat API - Development")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root() -> dict:
    return {
        "message": "LocalHub 챗봇 개발 서버",
        "health": "/api/chat/health",
        "docs": "/docs",
    }
