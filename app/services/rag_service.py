# app/services/rag_service.py

from operator import itemgetter
from typing import Dict, Any, Optional, List

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_community.vectorstores import Chroma
from langchain_ollama import ChatOllama

from app.models.query import QuerySource
from app.services.embedding_service import EmbeddingService


class RAGService:
    """RAG 파이프라인을 구성하고 질의를 처리하는 서비스"""

    def __init__(
            self,
            embedding_service: EmbeddingService,
            llm_model_name: str,
            chroma_persist_dir: str,
            chroma_collection_name: str
    ):
        self.embedding_function = embedding_service.get_embedding_function()
        self.vector_store = Chroma(
            collection_name=chroma_collection_name,
            embedding_function=self.embedding_function,
            persist_directory=chroma_persist_dir,
        )
        self.llm = ChatOllama(model=llm_model_name)

        # 프롬프트 템플릿 정의
        template = """
        당신은 법률 문서 분석 전문가입니다. 제공된 컨텍스트 정보만을 바탕으로 사용자의 질문에 답변해주세요.
        답변은 한국어로 작성해주세요. 컨텍스트에서 답을 찾을 수 없다면, "제공된 정보만으로는 답변하기 어렵습니다."라고 말하세요. 추측해서 답변하지 마세요.

        컨텍스트:
        {context}

        질문:
        {question}

        답변:
        """
        self.prompt = ChatPromptTemplate.from_template(template)

    def _create_retriever(self, tenant_id: Optional[str], document_type: Optional[str], top_k: int):
        """필터 조건에 맞는 Retriever를 생성합니다."""
        search_kwargs = {"k": top_k}

        # --- 핵심 수정 부분 ---
        filter_conditions = []
        if tenant_id:
            filter_conditions.append({"tenant_id": {"$eq": tenant_id}})
        if document_type:
            filter_conditions.append({"document_type": {"$eq": document_type}})

        if filter_conditions:
            # 조건이 하나일 때는 $and 가 필요 없지만, 일관성을 위해 항상 $and 구조 사용
            search_kwargs["filter"] = {"$and": filter_conditions}
        # --------------------

        return self.vector_store.as_retriever(search_kwargs=search_kwargs)

    def _format_docs(self, docs: List[Document]) -> str:
        """검색된 문서 청크들을 LLM 프롬프트에 넣기 좋은 형태로 포맷합니다."""
        return "\n\n".join(f"출처: {doc.metadata.get('source', '알 수 없음')}\n내용: {doc.page_content}" for doc in docs)

    def query(self, query_text: str, tenant_id: Optional[str], document_type: Optional[str], top_k: int) -> Dict:
        """사용자 질의를 처리하고 답변과 소스를 반환"""
        retriever = self._create_retriever(tenant_id, document_type, top_k)

        rag_chain = (
            RunnablePassthrough.assign(context=(lambda x: x["question"]) | retriever | self._format_docs)
            .assign(answer=(self.prompt | self.llm | StrOutputParser()))
        )

        # 소스 문서도 함께 가져오기 위한 체인
        chain_with_sources = RunnablePassthrough.assign(
            docs=itemgetter("question") | retriever
        ).assign(
            result=rag_chain
        )

        # 체인 실행
        result = chain_with_sources.invoke({"question": query_text})

        # 응답 형식에 맞게 소스 포맷팅
        sources = [
            QuerySource(
                source=doc.metadata.get("source", "알 수 없음"),
                content=doc.page_content,
                metadata=doc.metadata,
            ) for doc in result["docs"]
        ]

        return {
            "answer": result["result"]["answer"],
            "sources": sources
        }

