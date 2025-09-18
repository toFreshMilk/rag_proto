# app/config.py

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    프로젝트의 모든 설정을 관리하는 클래스
    환경 변수나 .env 파일에서도 값을 읽어올 수 있습니다.
    """
    # 모델 설정
    EMBEDDING_MODEL: str = "jhgan/ko-sroberta-multitask"
    OLLAMA_MODEL: str = "gemma:2b"

    # 벡터 DB (Chroma) 설정
    CHROMA_PERSIST_DIR: str = "/media/dev/a/ragdata/buptle_rag_proto/chroma_db"  #
    CHROMA_COLLECTION_NAME: str = "buptle_rag_collection"

    # 문서 처리 설정
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # 임시 파일 저장 경로
    UPLOAD_DIR: str = "uploaded_files"

    # pydantic-settings 설정
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')

@lru_cache
def get_settings() -> Settings:
    """설정 객체를 반환하는 함수 (캐싱 사용)"""
    return Settings()
