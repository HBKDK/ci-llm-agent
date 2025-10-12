"""
PostgreSQL 데이터베이스 연결
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base

# 환경변수에서 DB 설정 가져오기
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "ci_agent")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# SQLite fallback for local development
if os.getenv("USE_SQLITE", "false").lower() == "true":
    DATABASE_URL = "sqlite:///./data/ci_agent.db"

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    """데이터베이스 초기화"""
    Base.metadata.create_all(engine)


def get_db():
    """데이터베이스 세션 가져오기"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

