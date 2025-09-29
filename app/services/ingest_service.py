# app/services/ingest_service.py

import os
from pathlib import Path
from typing import Optional, Dict
from fastapi import UploadFile
from sqlalchemy.orm import Session

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader
from langchain_postgres.vectorstores import PGVector

from app.config import Settings
from app.models.clause import Document  # SQLAlchemy 모델 임포트


class IngestService:
    """문서 인덱싱(분할, 임베딩, 저장)을 담당하는 서비스"""

    def __init__(
            self,
            db_session: Session,
            settings: Settings,
            vector_store: PGVector
    ):
        self.db_session = db_session
        self.settings = settings
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.CHUNK_SIZE,
            chunk_overlap=self.settings.CHUNK_OVERLAP
        )
        self.vector_store = vector_store

    async def ingest_file(self, file: UploadFile, metadata: Dict):
        """
        단일 파일을 처리하여 RDB에 메타데이터를, Vector DB에 청크를 저장합니다.
        """
        upload_dir = Path(self.settings.UPLOAD_DIR)
        upload_dir.mkdir(exist_ok=True)
        file_path = upload_dir / f"{Path(file.filename).stem}_{os.urandom(4).hex()}{Path(file.filename).suffix}"

        try:
            # 1. 파일 시스템에 임시 저장
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())

            # 2. RDB에 Document 메타데이터 저장
            document = Document(
                tenant_id=metadata.get("tenant_id"),
                document_type=metadata.get("document_type"),
                original_filename=file.filename
            )
            self.db_session.add(document)
            self.db_session.commit()
            self.db_session.refresh(document)

            # 3. 문서 로드
            if file_path.suffix.lower() == ".pdf":
                loader = PyPDFLoader(str(file_path))
            elif file_path.suffix.lower() == ".docx":
                loader = UnstructuredWordDocumentLoader(str(file_path), mode="single")
            else:
                raise ValueError(f"지원하지 않는 파일 형식: {file_path.suffix}")

            docs = loader.load()

            # 4. 문서 분할 (Text Splitting)
            chunks = self.text_splitter.split_documents(docs)

            # 5. 각 청크에 메타데이터 추가 (RDB document id 포함)
            # 이 document_id를 통해 벡터 검색 결과와 RDB의 원본 문서 정보를 연결할 수 있습니다.
            for chunk in chunks:
                chunk.metadata["document_id"] = document.id
                chunk.metadata["original_filename"] = file.filename
                if metadata.get("tenant_id"):
                    chunk.metadata["tenant_id"] = metadata.get("tenant_id")
                if metadata.get("document_type"):
                    chunk.metadata["document_type"] = metadata.get("document_type")

            # 6. PGVector에 청크 저장
            self.vector_store.add_documents(chunks)

        finally:
            # 7. 임시 파일 삭제
            if file_path.exists():
                os.remove(file_path)

