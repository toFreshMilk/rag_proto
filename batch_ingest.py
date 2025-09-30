# scripts/batch_ingest.py

import os
import asyncio
from pathlib import Path
import logging
from dotenv import load_dotenv

# .env 파일 로드를 가장 먼저 실행
load_dotenv()

# 로깅 기본 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 필요한 모듈 임포트 ---
from app.config import settings
from app.models.base import Base  # SQLAlchemy Base 모델 임포트
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.ingest_service import IngestService
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService

# 비동기 DB 세션 설정 (비동기 URL 사용)
async_engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


async def main():
    """스크립트의 메인 실행 함수"""
    logger.info("=" * 50)
    logger.info("======= 단일 파일 인덱싱 배치 작업 시작 =======")
    logger.info("=" * 50)

    target_file_path = settings.TARGET_FILE
    logger.info(f".env 파일에서 다음 대상 파일을 읽어왔습니다: {target_file_path}")

    if not os.path.isfile(target_file_path):
        logger.error(f"!!! 치명적 오류: 지정된 테스트 파일이 존재하지 않습니다: {target_file_path}")
        return

    # --- ✨✨✨ 최종 해결 지점: 테이블을 삭제하고 다시 생성하는 로직으로 변경 ✨✨✨ ---
    logger.info("--- [단계 1/4] DB 스키마 및 데이터 초기화 시작 ---")
    async with async_engine.begin() as conn:
        # PGVector 테이블(컬렉션) 먼저 삭제
        logger.info(f"PGVector 테이블 '{settings.PGVECTOR_COLLECTION_NAME}'을 삭제합니다 (존재 시).")
        await conn.execute(text(f"DROP TABLE IF EXISTS {settings.PGVECTOR_COLLECTION_NAME} CASCADE;"))

        # SQLAlchemy 모델 테이블들(documents, clauses) 삭제
        logger.info("SQLAlchemy 모델 테이블(documents, clauses)을 삭제합니다 (존재 시).")
        await conn.run_sync(Base.metadata.drop_all)

        # 최신 모델 기준으로 테이블들 다시 생성
        logger.info("최신 모델 기준으로 모든 테이블을 다시 생성합니다.")
        await conn.run_sync(Base.metadata.create_all)
    logger.info("--- [단계 1/4] DB 스키마 및 데이터 초기화 완료 ---\n")

    logger.info(f"--- [단계 2/4] 파일 인덱싱 시작: {Path(target_file_path).name} ---")
    async with AsyncSessionLocal() as db_session:
        try:
            logger.info("서비스 의존성(임베딩, 벡터저장소) 생성 중...")
            embedding_service = EmbeddingService(model_name=settings.EMBEDDING_MODEL_NAME,
                                                 device=settings.EMBEDDING_MODEL_DEVICE)

            vector_store_service = VectorStoreService(
                connection=settings.SYNC_DATABASE_URL,
                collection_name=settings.PGVECTOR_COLLECTION_NAME,
                embeddings=embedding_service.get_embedding_function()
            )
            pg_vector_instance = vector_store_service.get_store()
            logger.info("서비스 의존성 생성 완료 (PGVector는 동기 연결 사용).")

            logger.info("\n--- [단계 3/4] IngestService 생성 및 실행 ---")
            ingest_service = IngestService(db_session=db_session, settings=settings, vector_store=pg_vector_instance)

            metadata = {"document_type": "contract", "tenant_id": "single_test"}
            await ingest_service.ingest_file(target_file_path, metadata)

            logger.info(f"--- [단계 4/4] 단일 파일 처리 성공: {Path(target_file_path).name} ---\n")

        except Exception as e:
            logger.critical(f"!!! 배치 작업 중 처리되지 않은 심각한 예외 발생: {e}", exc_info=True)

    logger.info("=" * 50)
    logger.info("======= 단일 파일 인덱싱 배치 작업 종료 =======")
    logger.info("=" * 50)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"!!! 최상위 레벨에서 오류 발생: {e}", exc_info=True)
