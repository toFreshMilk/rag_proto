import os
import shutil
import tempfile
import uuid
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.config import API_PREFIX, create_directories, RAW_DATA_DIR
from app.models.api import (
    UploadRequest, UploadResponse,
    QueryRequest, QueryResponse
)
from app.services.rag_service import RAGService

# 필요한 디렉토리 생성
create_directories()

# FastAPI 앱 생성
app = FastAPI(
    title="BuptleBiz RAG API",
    description="법틀비즈 RAG 프로토타입 API",
    version="0.1.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 환경에서는 특정 출처만 허용하도록 변경 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# RAG 서비스 초기화
rag_service = RAGService()


@app.get("/")
async def root():
    return {"message": "BuptleBiz RAG API에 오신 것을 환영합니다!"}


@app.post(f"{API_PREFIX}/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    tenant_id: Optional[str] = Form(None),
    document_type: str = Form(...),
    custom_metadata: Optional[str] = Form(None)
):
    """문서 업로드 및 인덱싱 엔드포인트"""
    try:
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # 업로드된 파일 내용 저장
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name

        # 메타데이터 구성
        metadata = {
            "tenant_id": tenant_id,
            "document_type": document_type,
            "original_filename": file.filename,
        }
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import upload, query

app = FastAPI(
    title="법률 문서 RAG 시스템",
    description="법률 문서를 인덱싱하고 질의에 응답하는 RAG 시스템 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(upload.router, prefix="/api", tags=["문서"])
app.include_router(query.router, prefix="/api", tags=["질의"])


@app.get("/")
async def root():
    return {
        "message": "법률 문서 RAG 시스템 API에 오신 것을 환영합니다",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
        # 사용자 정의 메타데이터 추가
        if custom_metadata:
            import json
            try:
                custom_metadata_dict = json.loads(custom_metadata)
                metadata["custom_metadata"] = custom_metadata_dict
            except json.JSONDecodeError:
                pass

        # RAG 서비스로 문서 처리
        document_id = rag_service.process_document(temp_file_path, metadata)

        # 원본 파일 저장 (선택 사항)
        original_filename = file.filename
        file_extension = os.path.splitext(original_filename)[1]
        saved_filename = f"{document_id}{file_extension}"
        saved_path = os.path.join(RAW_DATA_DIR, saved_filename)
        shutil.copy(temp_file_path, saved_path)

        # 임시 파일 삭제
        os.unlink(temp_file_path)

        return UploadResponse(
            success=True,
            document_id=document_id,
            message="문서 업로드 및 인덱싱이 완료되었습니다.",
            metadata=metadata
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"문서 처리 중 오류가 발생했습니다: {str(e)}"
        )


@app.post(f"{API_PREFIX}/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """질의 처리 엔드포인트"""
    try:
        response = rag_service.query(request)
        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"질의 처리 중 오류가 발생했습니다: {str(e)}"
        )


@app.get(f"{API_PREFIX}/health")
async def health_check():
    """서버 상태 확인 엔드포인트"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    from app.config import HOST, PORT

    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
