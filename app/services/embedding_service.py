from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from app.models.document import DocumentChunk
from app.config import EMBEDDING_MODEL_NAME


class EmbeddingService:
    """텍스트 임베딩을 위한 서비스 클래스"""

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        """초기화

        Args:
            model_name: 사용할 임베딩 모델 이름
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed_text(self, text: str) -> List[float]:
        """텍스트를 임베딩 벡터로 변환"""
        return self.model.encode(text).tolist()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """텍스트 목록을 임베딩 벡터 목록으로 변환"""
        return self.model.encode(texts).tolist()

    def embed_document_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """문서 청크 목록의 텍스트를 임베딩하고 청크에 저장"""
        texts = [chunk.text for chunk in chunks]
        embeddings = self.embed_texts(texts)

        # 임베딩 결과를 각 청크에 저장
        for i, chunk in enumerate(chunks):
            chunk.embedding = embeddings[i]

        return chunks

    def embed_query(self, query: str) -> List[float]:
        """검색 쿼리를 임베딩 벡터로 변환"""
        return self.embed_text(query)
