# app/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # .env 파일에서 아래 변수들을 읽어옵니다.

    # PostgreSQL 데이터베이스 연결 정보
    DATABASE_URL: str

    # PGVector 설정
    PGVECTOR_COLLECTION_NAME: str = "buptle_rag_collection"

    # 임베딩 모델 설정
    EMBEDDING_MODEL_NAME: str = "ko-sroberta-multitask"
    EMBEDDING_MODEL_DEVICE: str = "cpu"

    # LLM 모델 설정 (Ollama)
    LLM_MODEL_NAME: str = "qwen2:7b"

    # 문서 분할 설정
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # 임시 파일 저장 경로
    UPLOAD_DIR: str = "/tmp/rag_uploads"

    # .env 파일에 존재하여 추가된 필드 (현재 직접 사용되지는 않음)
    LOCAL_DOCS_PATH: str

    # .env 파일을 읽도록 설정
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


# 설정 클래스의 인스턴스를 생성합니다.
# 이제 다른 모듈에서 'from app.config import settings'로 가져올 수 있습니다.
settings = Settings()


# FastAPI 의존성 주입을 위해 캐시된 함수도 제공합니다.
@lru_cache()
def get_settings():
    return settings
