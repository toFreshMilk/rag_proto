import os
from pathlib import Path

# 기본 경로 설정
BASE_DIR = Path(__file__).resolve().parent.parent

# 데이터 디렉토리 설정
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")

# ChromaDB 설정
CHROMA_DB_DIR = os.path.join(BASE_DIR, "db", "chroma")

# 임베딩 모델 설정
EMBEDDING_MODEL_NAME = "jhgan/ko-sroberta-multitask"

# API 설정
API_PREFIX = "/api"

# 필요한 디렉토리 생성 함수
def create_directories():
    directories = [
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        CHROMA_DB_DIR
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# 서버 설정
HOST = "0.0.0.0"
PORT = 8000

# 추후 Milvus로 마이그레이션 시 필요한 설정
MILVUS_HOST = "localhost"
MILVUS_PORT = 19530
USE_MILVUS = False  # 기본값은 ChromaDB 사용
