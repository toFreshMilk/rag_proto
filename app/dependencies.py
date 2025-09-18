# app/dependencies.py

from functools import lru_cache

from app.config import get_settings
from app.services.rag_service import RAGService
from app.services.ingest_service import IngestService
from app.services.embedding_service import EmbeddingService

@lru_cache
def get_embedding_service() -> EmbeddingService:
    """EmbeddingService의 의존성 주입 함수."""
    settings = get_settings()
    return EmbeddingService(model_name=settings.EMBEDDING_MODEL)

@lru_cache
def get_rag_service() -> RAGService:
    """RAGService의 의존성 주입 함수."""
    settings = get_settings()
    return RAGService(
        embedding_service=get_embedding_service(),
        llm_model_name=settings.OLLAMA_MODEL,
        chroma_persist_dir=settings.CHROMA_PERSIST_DIR,
        chroma_collection_name=settings.CHROMA_COLLECTION_NAME
    )

@lru_cache
def get_ingest_service() -> IngestService:
    """IngestService의 의존성 주입 함수."""
    settings = get_settings()
    return IngestService(
        embedding_service=get_embedding_service(),
        chroma_persist_dir=settings.CHROMA_PERSIST_DIR,
        chroma_collection_name=settings.CHROMA_COLLECTION_NAME
    )

