# app/services/vector_store_service.py

from langchain_postgres.vectorstores import PGVector
from langchain_core.embeddings import Embeddings
import logging

logger = logging.getLogger(__name__)

class VectorStoreService:
    """PGVector 인스턴스 관리를 위한 서비스 (동기 방식 전용)"""
    def __init__(self, connection: str, collection_name: str, embeddings: Embeddings):
        self._connection = connection # 동기 DB URL을 전달받음
        self._collection_name = collection_name
        self._embeddings = embeddings
        self._store: PGVector | None = None
        logger.debug("VectorStoreService가 초기화되었습니다.")

    def get_store(self) -> PGVector:
        """
        초기화된 PGVector 인스턴스를 동기적으로 반환합니다.
        """
        if self._store is None:
            logger.info("PGVector 인스턴스가 존재하지 않아 새로 생성합니다. (동기 방식)")
            self._store = PGVector(
                embeddings=self._embeddings,
                collection_name=self._collection_name,
                connection=self._connection, # 동기 URL을 connection 파라미터에 전달
                use_jsonb=True, # 메타데이터 저장을 위해 권장
            )
            logger.info("PGVector 인스턴스 생성이 완료되었습니다.")
        else:
            logger.debug("기존에 캐시된 PGVector 인스턴스를 반환합니다.")
        return self._store
