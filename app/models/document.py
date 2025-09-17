from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Document(BaseModel):
    """문서 정보를 저장하는 모델"""
    id: Optional[str] = None
    content: str
    metadata: dict = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


class DocumentChunk(BaseModel):
    """문서 청크 정보를 저장하는 모델"""
    id: Optional[str] = None
    text: str
    metadata: dict = Field(default_factory=dict)
    embedding: Optional[List[float]] = None

    class Config:
        arbitrary_types_allowed = True


class DocumentMetadata(BaseModel):
    """문서 메타데이터 모델"""
    source: str
    title: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    document_type: str  # 'contract', 'legal_advice', 'statistics' 등
    tenant_id: Optional[str] = None  # 다중 테넌트 지원을 위한 필드
    custom_metadata: dict = Field(default_factory=dict)  # 추가 메타데이터

    class Config:
        arbitrary_types_allowed = True
