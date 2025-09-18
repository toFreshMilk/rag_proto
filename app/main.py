# app/main.py

import uvicorn
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import upload_router, query_router

# 로깅 기본 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = FastAPI(
    title="법틀비즈 RAG API",
    description="법률 문서 업로드, 인덱싱 및 질의응답을 위한 API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router.router, prefix="/api")
app.include_router(query_router.router, prefix="/api")

@app.get("/", summary="루트 경로", include_in_schema=False)
async def root():
    return {"message": "법틀비즈 RAG API 서버가 실행 중입니다. API 문서는 /docs 를 참고하세요."}

@app.get("/health", summary="헬스 체크")
async def health_check():
    """서비스가 정상적으로 실행 중인지 확인하는 엔드포인트입니다."""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

