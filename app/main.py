# app/main.py

from fastapi import FastAPI
from app.models import base
from app.database import engine
from app.routers import query_router, upload_router

# 애플리케이션 시작 시 데이터베이스 테이블 생성
# 실제 프로덕션에서는 Alembic과 같은 마이그레이션 도구를 사용하는 것이 좋습니다.
base.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BuptleBiz RAG System Prototype",
    version="0.2.0",
    description="문서 기반 질의응답을 위한 RAG API 프로토타입"
)

@app.get("/", summary="Health Check", include_in_schema=False)
def read_root():
    return {"status": "BuptleBiz RAG API is running!"}

# API 라우터 포함
app.include_router(upload_router.router, prefix="/api")
app.include_router(query_router.router, prefix="/api")

