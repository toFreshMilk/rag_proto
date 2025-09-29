# app/services/vector_store_service.py

from langchain_postgres.vectorstores import PGVector
from langchain_core.embeddings import Embeddings

class VectorStoreService:
    """PGVector 인스턴스 관리를 위한 서비스"""
    def __init__(self, connection: str, collection_name: str, embeddings: Embeddings):
        """
        PGVector 초기화
        Args:
            connection (str): PostgreSQL 연결 URL
            collection_name (str): 벡터 컬렉션 이름
            embeddings (Embeddings): 임베딩 함수 객체
        """
        # 라이브러리 변경에 따라 파라미터 이름을 connection, embeddings로 수정
        self._store = PGVector(
            connection=connection,
            collection_name=collection_name,
            embeddings=embeddings,
            use_jsonb=True # 메타데이터를 jsonb 타입으로 저장하여 유연성 확보
        )

    def get_store(self) -> PGVector:
        """초기화된 PGVector 인스턴스를 반환합니다."""
        return self._store
