# app/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

# 데이터베이스 엔진 생성
engine = create_engine(
    settings.DATABASE_URL
)

# 데이터베이스 세션 생성기
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# FastAPI 의존성 주입용 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
