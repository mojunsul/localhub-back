from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base

from app.routers import locations, posts

from app.chat.router import router as chat_router

# 서버 기동 시 SQLite 테이블 자동 생성
Base.metadata.create_all(bind=engine)

# FastAPI 객체 생성
app = FastAPI(title="LocalHub API Server", version="1.0")

# CORS 미들웨어 설정 (Netlify & Render 연동용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(locations.router)
app.include_router(posts.router)
app.include_router(chat_router)


@app.route("/", methods=["GET", "HEAD"])
async def read_root():
    return {"message": "LocalHub API Server is running!"}