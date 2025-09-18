# app/services/embedding_service.py

from langchain_huggingface import HuggingFaceEmbeddings

class EmbeddingService:
    """텍스트 임베딩을 전담하는 서비스 클래스"""
    def __init__(self, model_name: str):
        """
        초기화 시 임베딩 모델을 로드합니다.
        Args:
            model_name: 사용할 임베딩 모델 이름 (e.g., "ko-sroberta-multitask")
        """
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': False}
        )

    def get_embedding_function(self):
        """LangChain의 다른 컴포넌트에 전달할 임베딩 함수 객체를 반환합니다."""
        return self.embedding_model

