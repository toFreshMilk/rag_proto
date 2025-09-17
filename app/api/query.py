from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional

from app.models.api import QueryRequest, QueryResponse
from app.services.rag_service import RAGService

router = APIRouter()
rag_service = RAGService()

@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """문서 질의 및 응답 생성 엔드포인트"""
    try:
        # RAG 서비스로 질의 처리
        response = rag_service.query(request)
        return response

    except Exception as e:
        # 오류 발생 시 예외 발생
        raise HTTPException(status_code=500, detail=f"질의 처리 중 오류가 발생했습니다: {str(e)}")
