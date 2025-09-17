from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from typing import Dict, Any, Optional
import json
import os
import tempfile

from app.models.api import UploadRequest, UploadResponse
from app.services.rag_service import RAGService

router = APIRouter()
rag_service = RAGService()

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    tenant_id: Optional[str] = Form(None),
    document_type: str = Form(...),
    custom_metadata: Optional[str] = Form(None)
):
    """문서 파일 업로드 및 인덱싱 엔드포인트"""
    try:
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            # 파일 내용 쓰기
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        # 메타데이터 준비
        metadata = {
            "source": file.filename,
            "content_type": file.content_type,
            "document_type": document_type,
        }

        # 테넌트 ID 추가 (있는 경우)
        if tenant_id:
            metadata["tenant_id"] = tenant_id

        # 커스텀 메타데이터 추가 (있는 경우)
        if custom_metadata:
            try:
                custom_meta_dict = json.loads(custom_metadata)
                metadata.update(custom_meta_dict)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid custom metadata JSON format")

        # RAG 서비스로 문서 처리
        document_id = rag_service.process_document(temp_path, metadata)

        # 임시 파일 삭제
        os.unlink(temp_path)

        return UploadResponse(
            success=True,
            document_id=document_id,
            message="문서가 성공적으로 업로드되고 인덱싱되었습니다."
        )

    except Exception as e:
        # 오류 발생 시 임시 파일 정리 시도
        try:
            if 'temp_path' in locals():
                os.unlink(temp_path)
        except:
            pass

        # 오류 응답 반환
        return UploadResponse(
            success=False,
            message=f"문서 처리 중 오류가 발생했습니다: {str(e)}"
        )
