# app/services/embedding_service.py

from langchain_huggingface import HuggingFaceEmbeddings

class EmbeddingService:
    """텍스트 임베딩을 전담하는 서비스 클래스"""
    def __init__(self, model_name: str, device: str = "cpu"):
        """
        초기화 시 임베딩 모델을 로드합니다.
        Args:
            model_name: 사용할 임베딩 모델 이름 (e.g., "ko-sroberta-multitask")
            device: 모델을 로드할 장치 (e.g., "cpu", "cuda")
        """
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': device},
            encode_kwargs={'normalize_embeddings': True} # 유사도 계산 시 코사인 유사도를 사용하기 위해 정규화하는 것이 일반적
        )

    def get_embedding_function(self):
        """LangChain의 다른 컴포넌트에 전달할 임베딩 함수 객체를 반환합니다."""
        return self.embedding_model
