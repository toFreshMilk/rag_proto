# scripts/batch_ingest.py

import os
import asyncio
from pathlib import Path
from typing import List
import logging

# SQLAlchemy 세션을 생성하기 위한 설정
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# 기존에 만들어 둔 서비스와 모델, 설정들을 그대로 재활용합니다.
from app.config import settings
from app.services.ingest_service import IngestService
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService
from app.models.clause import Document

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- FastAPI 밖에서 SQLAlchemy 세션을 사용하기 위한 설정 ---
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_processed_files() -> set:
    """데이터베이스에서 이미 처리된 파일 이름 목록을 가져옵니다."""
    db = SessionLocal()
    try:
        stmt = select(Document.original_filename)
        result = db.execute(stmt)
        processed_files = {row[0] for row in result}
        logger.info(f"총 {len(processed_files)}개의 기처리된 파일을 확인했습니다.")
        return processed_files
    finally:
        db.close()


async def main(docs_path: str, batch_size: int):
    """
    지정된 경로의 문서들을 배치 단위로 처리하여 인덱싱합니다.
    """
    logger.info("배치 인덱싱 스크립트를 시작합니다.")

    # 1. 서비스 초기화 (의존성 주입을 수동으로 처리)
    embedding_service = EmbeddingService(
        model_name=settings.EMBEDDING_MODEL_NAME,
        device=settings.EMBEDDING_MODEL_DEVICE
    )
    # VectorStoreService 초기화 파라미터 이름에 맞춰 수정
    vector_store_service = VectorStoreService(
        connection=settings.DATABASE_URL,
        collection_name=settings.PGVECTOR_COLLECTION_NAME,
        embeddings=embedding_service.get_embedding_function()
    )

    # 2. 처리할 파일 목록 준비
    docs_path = Path(docs_path)
    if not docs_path.is_dir():
        logger.error(f"지정한 경로 '{docs_path}'를 찾을 수 없거나 디렉토리가 아닙니다.")
        return

    supported_extensions = {".pdf", ".docx"}
    all_files = [
        f for f in docs_path.glob("**/*")
        if f.is_file() and f.suffix.lower() in supported_extensions
    ]

    # 3. 이미 처리된 파일 건너뛰기 로직
    processed_files_set = get_processed_files()
    files_to_process = [
        f for f in all_files if f.name not in processed_files_set
    ]

    if not files_to_process:
        logger.info("새롭게 처리할 문서가 없습니다. 모든 문서가 최신 상태입니다.")
        return

    logger.info(f"총 {len(all_files)}개 파일 중, {len(files_to_process)}개를 처리합니다.")

    # 4. 배치 처리
    files_to_process_batch = files_to_process[:batch_size]
    logger.info(f"이번 배치에서는 {len(files_to_process_batch)}개 문서를 처리합니다.")

    for file_path in files_to_process_batch:
        db_session = SessionLocal()
        ingest_service = IngestService(
            db_session=db_session,
            settings=settings,
            vector_store=vector_store_service.get_store()
        )

        logger.info(f"'{file_path.name}' 파일 처리 시작...")
        try:
            with open(file_path, "rb") as f:
                from fastapi import UploadFile
                mock_upload_file = UploadFile(filename=file_path.name, file=f)

                metadata = {"document_type": "contract", "tenant_id": "default_tenant"}

                await ingest_service.ingest_file(mock_upload_file, metadata)

            logger.info(f"✅ '{file_path.name}' 파일 처리 완료.")

        except Exception as e:
            logger.error(f"❌ '{file_path.name}' 파일 처리 중 오류 발생: {e}", exc_info=True)
            db_session.rollback()
        finally:
            db_session.close()

    logger.info("배치 인덱싱 작업을 완료했습니다.")


if __name__ == "__main__":
    DOCUMENT_DIRECTORY = os.getenv("LOCAL_DOCS_PATH")
    BATCH_SIZE = 10

    # 배치 스크립트를 실행할 때 'python -m scripts.batch_ingest' 와 같이 모듈로 실행해야 합니다.
    asyncio.run(main(DOCUMENT_DIRECTORY, BATCH_SIZE))

