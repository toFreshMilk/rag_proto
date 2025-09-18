# app/services/ingest_service.py

import os
from pathlib import Path
from typing import Optional, Dict
from fastapi import UploadFile

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader
from langchain_community.vectorstores import Chroma

from app.config import get_settings
from app.services.embedding_service import EmbeddingService


class IngestService:
    """문서 인덱싱(분할, 임베딩, 저장)을 담당하는 서비스"""

    def __init__(
            self,
            embedding_service: EmbeddingService,
            chroma_persist_dir: str,
            chroma_collection_name: str
    ):
        self.settings = get_settings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.CHUNK_SIZE,
            chunk_overlap=self.settings.CHUNK_OVERLAP
        )
        self.embedding_function = embedding_service.get_embedding_function()
        self.vector_store = Chroma(
            collection_name=chroma_collection_name,
            embedding_function=self.embedding_function,
            persist_directory=chroma_persist_dir,
        )

    async def ingest_file(self, file: UploadFile, metadata: Optional[Dict] = None):
        """단일 파일을 처리하여 DB에 저장. 업로드 시 전달된 공통 메타데이터를 각 문서 청크에 추가합니다."""
        upload_dir = Path(self.settings.UPLOAD_DIR)
        upload_dir.mkdir(exist_ok=True)
        file_path = upload_dir / file.filename

        try:
            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())

            if file_path.suffix.lower() == ".pdf":
                loader = PyPDFLoader(str(file_path))
            elif file_path.suffix.lower() == ".docx":
                loader = UnstructuredWordDocumentLoader(str(file_path))
            else:
                raise ValueError(f"지원하지 않는 파일 형식: {file_path.suffix}")

            documents = loader.load()
            chunks = self.text_splitter.split_documents(documents)

            if metadata:
                for chunk in chunks:
                    chunk.metadata.update(metadata)

            self.vector_store.add_documents(chunks)

        finally:
            if file_path.exists():
                os.remove(file_path)

