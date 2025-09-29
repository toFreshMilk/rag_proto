# app/services/rag_service.py

from operator import itemgetter
from typing import Dict, Optional, List

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_postgres.vectorstores import PGVector
from langchain_ollama import ChatOllama

from app.models.query import QuerySource


class RAGService:
    """RAG 파이프라인을 구성하고 질의를 처리하는 서비스"""

    def __init__(self, llm_model_name: str, vector_store: PGVector):
        self.vector_store = vector_store
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

        filter_conditions = {}
        if tenant_id:
            filter_conditions["tenant_id"] = tenant_id
        if document_type:
            filter_conditions["document_type"] = document_type

        if filter_conditions:
            search_kwargs["filter"] = filter_conditions

        return self.vector_store.as_retriever(search_kwargs=search_kwargs)

    def _format_docs(self, docs: List[Document]) -> str:
        """검색된 문서 청크들을 LLM 프롬프트에 넣기 좋은 형태로 포맷합니다."""
        return "\n\n".join(
            f"출처 파일: {doc.metadata.get('original_filename', '알 수 없음')}\n내용: {doc.page_content}" for doc in docs)

    def query(self, query_text: str, tenant_id: Optional[str], document_type: Optional[str], top_k: int) -> Dict:
        """사용자 질의를 처리하고 답변과 소스를 반환"""
        retriever = self._create_retriever(tenant_id, document_type, top_k)

        rag_chain = (
            RunnablePassthrough.assign(context=itemgetter("question") | retriever | self._format_docs)
            .assign(answer=(self.prompt | self.llm | StrOutputParser()))
        )

        chain_with_sources = RunnablePassthrough.assign(
            docs=itemgetter("question") | retriever
        ).assign(
            result=rag_chain
        )

        result = chain_with_sources.invoke({"question": query_text})

        sources = [
            QuerySource(
                source=doc.metadata.get('original_filename', '알 수 없음'),
                content=doc.page_content,
                metadata=doc.metadata,
                score=doc.metadata.get('_score')  # PGVector는 관련성 점수를 _score로 반환할 수 있음
            ) for doc in result["docs"]
        ]

        return {
            "answer": result["result"]["answer"],
            "sources": sources
        }
