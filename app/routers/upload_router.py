# app/routers/upload_router.py

import logging
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Response

from app.services.ingest_service import IngestService
from app.dependencies import get_ingest_service
from app.models.query import UploadResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["문서 관리"])


@router.post("/upload", response_model=UploadResponse, summary="문서 업로드 및 인덱싱")
async def upload_document(
        response: Response,
        files: List[UploadFile] = File(..., description="업로드할 문서 파일 (PDF, DOCX)"),
        tenant_id: Optional[str] = Form(None, description="문서가 속한 고객사(테넌트) ID"),
        document_type: str = Form("general", description="문서의 종류 (예: contract, legal_advice)"),
        ingest_service: IngestService = Depends(get_ingest_service)
):
    """하나 이상의 문서를 메타데이터와 함께 업로드하여 벡터 DB에 저장합니다."""
    if not files:
        raise HTTPException(status_code=400, detail="업로드할 파일이 없습니다.")

    base_metadata = {"document_type": document_type}
    if tenant_id:
        base_metadata["tenant_id"] = tenant_id

    processed_files = []
    errors = []
    for file in files:
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in {".pdf", ".docx"}:
            error_msg = f"'{file.filename}' 파일은 지원하지 않는 형식입니다."
            errors.append({"file": file.filename, "error": error_msg})
            logger.warning(error_msg)
            continue

        try:
            await ingest_service.ingest_file(file, base_metadata)
            processed_files.append(file.filename)
            logger.info(f"문서 '{file.filename}'가 인덱싱되었습니다. (Tenant: {tenant_id})")
        except Exception as e:
            logger.error(f"'{file.filename}' 파일 처리 중 오류 발생: {e}", exc_info=True)
            errors.append({"file": file.filename, "error": str(e)})

    if errors and not processed_files:
        raise HTTPException(status_code=500, detail={"message": "모든 파일 처리 중 오류 발생", "errors": errors})

    # 일부 파일만 실패한 경우를 위해 상태 코드 조정 (207: Multi-Status)
    response.status_code = 207 if errors else 200

    return UploadResponse(processed_files=processed_files, errors=errors)

