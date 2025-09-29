# app/services/vector_store_service.py

from langchain_postgres.vectorstores import PGVector

class VectorStoreService:
    """PGVector 인스턴스 관리를 위한 서비스"""
    def __init__(self, db_url: str, collection_name: str, embedding_function):
        """
        PGVector 초기화
        Args:
            db_url (str): PostgreSQL 연결 URL
            collection_name (str): 벡터 컬렉션 이름
            embedding_function: 임베딩 함수
        """
        self._store = PGVector(
            connection_string=db_url,
            collection_name=collection_name,
            embedding_function=embedding_function,
        )

    def get_store(self) -> PGVector:
        """초기화된 PGVector 인스턴스를 반환합니다."""
        return self._store
