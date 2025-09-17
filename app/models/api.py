from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import UploadFile, File, Form


class UploadRequest(BaseModel):
    """문서 업로드 요청 모델"""
    tenant_id: Optional[str] = None
    document_type: str
    metadata: Optional[Dict[str, Any]] = None
    file_name: Optional[str] = None
    file_content_type: Optional[str] = None
    custom_metadata: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "tenant_id": "client123",
                "document_type": "legal_advice",
                "metadata": {
                    "author": "홍길동",
                    "category": "계약법",
                    "importance": "high"
                }
            }
        }


class UploadResponse(BaseModel):
    """문서 업로드 응답 모델"""
    success: bool
    document_id: Optional[str] = None
    message: Optional[str] = None


class QueryRequest(BaseModel):
    """문서 질의 요청 모델"""
    query: str
    tenant_id: Optional[str] = None
    top_k: int = 3
    filters: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "query": "계약서에서 중요한 법적 고려사항은 무엇인가요?",
                "tenant_id": "client123",
                "top_k": 3,
                "filters": {
                    "document_type": "legal_advice"
                }
            }
        }


class QueryResponseSource(BaseModel):
    """질의 응답 소스 모델"""
    document_id: str
    source: str
    title: Optional[str] = None
    document_type: Optional[str] = None
    text: str
    relevance_score: float
    metadata: Optional[Dict[str, Any]] = None


class QueryResponse(BaseModel):
    """문서 질의 응답 모델"""
    query: str
    answer: str
    sources: List[QueryResponseSource] = []
    similar_cases: Optional[List[Dict[str, Any]]] = None
    suggestions: Optional[List[str]] = None
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
