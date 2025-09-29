# app/dependencies.py

from functools import lru_cache
from sqlalchemy.orm import Session
from fastapi import Depends

from app.config import settings as app_settings
from app.database import get_db
from app.services.rag_service import RAGService
from app.services.ingest_service import IngestService
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService

@lru_cache
def get_embedding_service() -> EmbeddingService:
    """EmbeddingService의 의존성 주입 함수 (캐시됨)"""
    return EmbeddingService(
        model_name=app_settings.EMBEDDING_MODEL_NAME,
        device=app_settings.EMBEDDING_MODEL_DEVICE
    )

@lru_cache
def get_vector_store_service(
    embedding_service: EmbeddingService = Depends(get_embedding_service)
) -> VectorStoreService:
    """VectorStoreService의 의존성 주입 함수 (캐시됨)"""
    # VectorStoreService 초기화 파라미터 이름에 맞춰 수정
    return VectorStoreService(
        connection=app_settings.DATABASE_URL,
        collection_name=app_settings.PGVECTOR_COLLECTION_NAME,
        embeddings=embedding_service.get_embedding_function()
    )

def get_ingest_service(
    db: Session = Depends(get_db),
    vector_store_service: VectorStoreService = Depends(get_vector_store_service)
) -> IngestService:
    """IngestService의 의존성 주입 함수 (요청마다 생성)"""
    return IngestService(
        db_session=db,
        settings=app_settings,
        vector_store=vector_store_service.get_store()
    )

def get_rag_service(
    vector_store_service: VectorStoreService = Depends(get_vector_store_service)
) -> RAGService:
    """RAGService의 의존성 주입 함수 (요청마다 생성)"""
    return RAGService(
        llm_model_name=app_settings.LLM_MODEL_NAME,
        vector_store=vector_store_service.get_store()
    )
