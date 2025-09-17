import os
import uuid
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings
from app.models.document import DocumentChunk
from app.config import CHROMA_DB_DIR, USE_MILVUS, MILVUS_HOST, MILVUS_PORT


class StorageService:
    """벡터 데이터베이스 저장 및 검색 서비스"""

    def __init__(self, collection_name: str = "buptle_documents"):
        """초기화

        Args:
            collection_name: 사용할 컬렉션 이름
        """
        self.collection_name = collection_name

        if USE_MILVUS:
            # Milvus 연결 설정 (추후 구현)
            raise NotImplementedError("Milvus 연결은 아직 구현되지 않았습니다.")
        else:
            # ChromaDB 설정
            self.client = chromadb.PersistentClient(
                path=CHROMA_DB_DIR,
                settings=Settings(
                    anonymized_telemetry=False
                )
            )

            # 컬렉션 가져오기 또는 생성
            try:
                self.collection = self.client.get_collection(name=collection_name)
            except ValueError:
                self.collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"description": "법틀비즈 문서 저장소"}
                )

    def add_document_chunks(self, chunks: List[DocumentChunk]) -> List[str]:
        """문서 청크를 벡터 저장소에 추가"""
        if not chunks:
            return []

        ids = [chunk.id for chunk in chunks]
        texts = [chunk.text for chunk in chunks]
        embeddings = [chunk.embedding for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]

        # 청크 추가
        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )

        return ids

    def search_by_vector(self, 
                       query_vector: List[float], 
                       top_k: int = 5,
                       filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """벡터 쿼리로 유사한 문서 검색"""
        where = {}
        if filters:
            # tenant_id 필터링
            if 'tenant_id' in filters and filters['tenant_id']:
                where["tenant_id"] = filters["tenant_id"]

            # document_type 필터링
            if 'document_type' in filters and filters['document_type']:
                where["document_type"] = filters["document_type"]

        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=where if where else None
        )

        # 결과 포맷팅
        formatted_results = []
        for i in range(len(results["ids"][0])):
            formatted_results.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })

        return formatted_results

    def search_by_text(self, 
                      query_text: str, 
                      top_k: int = 5,
                      filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """텍스트 쿼리로 유사한 문서 검색 (임베딩 서비스 필요)"""
        where = {}
        if filters:
            # tenant_id 필터링
            if 'tenant_id' in filters and filters['tenant_id']:
                where["tenant_id"] = filters["tenant_id"]

            # document_type 필터링
            if 'document_type' in filters and filters['document_type']:
                where["document_type"] = filters["document_type"]

        results = self.collection.query(
            query_texts=[query_text],
            n_results=top_k,
            where=where if where else None
        )

        # 결과 포맷팅
        formatted_results = []
        for i in range(len(results["ids"][0])):
            formatted_results.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })

        return formatted_results

    def delete_document(self, document_id: str) -> bool:
        """문서 ID로 문서 삭제"""
        try:
            self.collection.delete(ids=[document_id])
            return True
        except Exception as e:
            print(f"문서 삭제 중 오류 발생: {e}")
            return False

    def delete_documents_by_filter(self, filter_dict: Dict[str, Any]) -> int:
        """필터 조건에 맞는 문서 삭제"""
        try:
            # 필터 조건에 맞는 문서 검색
            results = self.collection.get(where=filter_dict)
            if not results or not results["ids"]:
                return 0

            # 검색된 문서 삭제
            self.collection.delete(ids=results["ids"])
            return len(results["ids"])
        except Exception as e:
            print(f"필터 기반 문서 삭제 중 오류 발생: {e}")
            return 0
