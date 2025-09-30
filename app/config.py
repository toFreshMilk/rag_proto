# app/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    """
    .env 파일의 설정 값들을 읽어와 관리하는 클래스.
    Pydantic을 통해 타입 검증 및 기본값 설정이 이루어집니다.
    """
    # --- 데이터베이스 ---
    DATABASE_URL: str         # 비동기 ORM용
    SYNC_DATABASE_URL: str    # 동기 라이브러리용 (PGVector)
    PGVECTOR_COLLECTION_NAME: str

    # --- 임베딩 모델 ---
    EMBEDDING_MODEL_NAME: str
    EMBEDDING_MODEL_DEVICE: str
    VECTOR_SIZE: int

    # --- LLM 모델 ---
    LLM_MODEL_NAME: str

    # --- 파일 경로 ---
    LOCAL_DOCS_PATH: str
    TARGET_FILE: str
    UPLOAD_DIR: str

    # .env 파일을 읽도록 설정
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

# 설정 클래스의 인스턴스를 생성. 애플리케이션 전역에서 사용.
settings = Settings()

@lru_cache()
def get_settings():
    """FastAPI 의존성 주입에서 사용할 캐시된 설정 함수"""
    return settings
