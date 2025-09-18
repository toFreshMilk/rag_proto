# app/routers/query_router.py

import logging
from fastapi import APIRouter, HTTPException, Depends

from app.models.query import QueryRequest, QueryResponse
from app.services.rag_service import RAGService
from app.dependencies import get_rag_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["질의응답"])

@router.post("/query", response_model=QueryResponse, summary="문서 기반 질의응답")
async def query_documents(
    request: QueryRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    사용자의 질문과 필터 조건을 받아 RAG 파이프라인을 통해 답변과 소스를 생성합니다.
    - **tenant_id**: 특정 고객사의 문서만 검색합니다.
    - **document_type**: 특정 종류의 문서만 검색합니다.
    """
    try:
        result = rag_service.query(
            query_text=request.query,
            tenant_id=request.tenant_id,
            document_type=request.document_type,
            top_k=request.top_k
        )
        return QueryResponse(**result)
    except Exception as e:
        logger.error(f"질의응답 처리 중 예외 발생: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="요청을 처리하는 중에 서버에서 오류가 발생했습니다."
        )

