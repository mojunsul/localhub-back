from sqlalchemy import Column, Integer, String, Text, Float, JSON, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category_id = Column(String(10), nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    addr1 = Column(String(255), nullable=True)
    addr2 = Column(String(255), nullable=True)
    tel = Column(String(50), nullable=True)
    mapx = Column(Float, nullable=True)
    mapy = Column(Float, nullable=True)
    firstimage = Column(String(500), nullable=True)
    extra_data = Column(JSON, nullable=True)


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    password = Column(String(100), nullable=False)  # RFP 명세 조항에 의거한 평문 저장
    views = Column(Integer, default=0, nullable=False)
    tags = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())