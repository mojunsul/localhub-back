# 디렉토리 위치: backend/app/database.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

# 1. 현재 database.py 파일이 있는 위치를 기준으로 부모(상위) 디렉토리 경로를 동적으로 계산합니다.
# 이렇게 하면 실행하는 위치가 어디든 상관없이 항상 backend/app/ 폴더 상위에 localhub.db를 가리킵니다.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "localhub.db")

# 2. SQLite 호환성용 URL 생성
# .env에 DATABASE_URL이 지정되어 있으면 그것을 쓰고, 없으면 방금 동적으로 계산한 안전한 경로를 사용합니다.
DEFAULT_DB_URL = f"sqlite:///{DB_PATH}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

# SQLite의 경우 백슬래시(\) 경로 인식을 위해 가공이 필요할 수 있으므로 안전하게 세팅합니다.
if DATABASE_URL.startswith("sqlite:///"):
    # 윈도우 환경 경로 매핑 호환성 보장
    db_file_path = DATABASE_URL.replace("sqlite:///", "")
    DATABASE_URL = f"sqlite:///{os.path.abspath(db_file_path)}"

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}  # SQLite 멀티스레드 접근 허용
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()