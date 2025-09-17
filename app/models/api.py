from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class UploadRequest(BaseModel):
    """문서 업로드 요청 모델"""
    tenant_id: Optional[str] = None
    document_type: str
    metadata: Optional[Dict[str, Any]] = None


class UploadResponse(BaseModel):
    """문서 업로드 응답 모델"""
    success: bool
    document_id: Optional[str] = None
    message: str
    metadata: Optional[Dict[str, Any]] = None


class QueryRequest(BaseModel):
    """검색 질의 요청 모델"""
    query: str
    tenant_id: Optional[str] = None
    top_k: int = 5
    filters: Optional[Dict[str, Any]] = None


class QueryResponseSource(BaseModel):
    """검색 결과의 출처 정보"""
    document_id: str
    source: str
    title: Optional[str] = None
    document_type: str
    text: str
    relevance_score: float
    metadata: Optional[Dict[str, Any]] = None


class QueryResponse(BaseModel):
    """검색 질의 응답 모델"""
    query: str
    answer: str
    sources: List[QueryResponseSource]
    metadata: Optional[Dict[str, Any]] = None
    similar_cases: Optional[List[Dict[str, Any]]] = None
    suggestions: Optional[List[str]] = None
