# app/models/query.py

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# --- Upload Endpoint ---
class UploadResponse(BaseModel):
    """문서 업로드 API의 응답 모델"""
    message: str = "요청이 처리되었습니다."
    processed_files: List[str] = Field(default_factory=list)
    errors: List[Dict] = Field(default_factory=list)


# --- Query Endpoint ---
class QueryRequest(BaseModel):
    """문서 질의 API의 요청 모델"""
    query: str = Field(..., description="사용자 질의 텍스트")
    tenant_id: Optional[str] = Field(None, description="테넌트 ID 필터")
    document_type: Optional[str] = Field(None, description="문서 유형 필터")
    top_k: int = Field(3, description="참조할 문서 청크의 최대 개수")


class QuerySource(BaseModel):
    """질의 응답에 참조된 소스 문서 정보"""
    source: str = Field(..., description="원본 파일 경로 또는 이름")
    content: str = Field(..., description="참조된 문서 청크의 내용")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="청크의 메타데이터")
    score: Optional[float] = Field(None, description="관련성 점수")


class QueryResponse(BaseModel):
    """문서 질의 API의 응답 모델"""
    answer: str = Field(..., description="LLM이 생성한 최종 답변")
    sources: List[QuerySource] = Field(..., description="답변의 근거가 된 소스 목록")

