# app/services/ingest_service.py

import os
import docx2txt
import json
from pathlib import Path
from typing import Dict, Union, List
import logging
from fastapi import UploadFile

from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.documents import Document as LangchainDocument
from langchain_postgres.vectorstores import PGVector
from langchain_openai import AzureChatOpenAI # Azure용 클래스 임포트
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.config import Settings
from app.models.clause import Document, Clause

logger = logging.getLogger(__name__)


class IngestService:
    def __init__(self, db_session: AsyncSession, settings: Settings, vector_store: PGVector):
        self.db_session = db_session
        self.settings = settings
        self.vector_store = vector_store

        # --- ✨✨✨ LLM 교체 (Azure OpenAI) ✨✨✨ ---
        self.llm = AzureChatOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_deployment=settings.AZURE_OPENAI_CHAT_DEPLOYMENT_NAME,
            temperature=0,
            # Azure API는 JSON 모드를 지원하므로, 프롬프트에서 강력하게 지시하는 것으로 충분
        )
        logger.info(f"Azure LLM 모델 '{settings.AZURE_OPENAI_CHAT_DEPLOYMENT_NAME}'이 초기화되었습니다.")

    def _get_structured_data_from_llm(self, document_text: str) -> List[Dict]:
        logger.info("OpenAI API를 통해 문서 구조화를 시작합니다.")

        system_prompt = """
        당신은 법률 문서를 분석하여 JSON 형식으로 구조화하는 최고의 전문가입니다.
        주어진 계약서 텍스트를 분석하고, 결과를 반드시 하나의 JSON 객체로만 출력해야 합니다.
        JSON 객체는 "clauses"라는 키를 가져야 하며, 그 값은 각 조항 정보를 담은 객체들의 배열입니다.
        다른 어떤 설명이나 서론, 결론도 없이 오직 JSON 객체만 출력하십시오.
        """

        human_prompt = """
        아래의 지시사항을 반드시 따라서 주어진 계약서 텍스트를 분석하고, 결과를 JSON 객체로 출력해 주십시오.

        **지시사항:**
        1. 계약서의 본문 내용만 분석하고, 양 당사자의 서명(날인)이 나타난 이후의 내용은 '첨부 자료'로 간주하여 완전히 무시하십시오.
        2. 본문 시작 전의 제목과 당사자 정보 등은 '서문'으로 간주하고, '조' 번호는 "0"으로, '항' 번호는 "1"로 지정하십시오.
        3. '제O조'에서 '조' 번호는 숫자만 추출하여 "clause_number"에 문자열로 할당하십시오.
        4. '조'의 제목을 "clause_title"에 할당하십시오.
        5. '항(①, ②...)', '호(1., 2...)', '목(가., 나...)'은 모두 "item_number"에 해당 마커('①', '1.', '가.')를 그대로 할당하십시오.
        6. 만약 '조' 아래에 명시적인 '항'이나 '호'가 없다면, 해당 '조'의 전체 내용을 하나의 항으로 간주하고 "item_number"를 "1"로 지정하십시오.

        **계약서 텍스트:**
        {document_text}
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt)
        ])

        # StrOutputParser는 LLM의 순수 텍스트 출력을 받아오고, json.loads로 파싱
        chain = prompt | self.llm | StrOutputParser()

        try:
            response_str = chain.invoke({"document_text": document_text})
            # LLM이 반환한 JSON 문자열을 파이썬 딕셔너리로 변환
            response_json = json.loads(response_str)

            clauses = response_json.get("clauses", [])
            logger.info(f"OpenAI API로부터 총 {len(clauses)}개의 구조화된 조항을 성공적으로 추출했습니다.")
            return clauses
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"LLM 결과 처리 중 오류 발생: {e}", exc_info=True)
            raise ValueError("OpenAI API로부터 유효한 'clauses' JSON 배열을 얻는 데 실패했습니다.")

    # ingest_file 메서드는 변경할 필요 없이 그대로 사용하면 됩니다.
    async def ingest_file(self, file_input: Union[UploadFile, str, Path], metadata: Dict):
        # (이전 답변과 동일한 로직)
        # ...
        # structured_clauses = self._get_structured_data_from_llm(text) 호출 부분 포함
        # ...
        file_path: Path
        filename: str
        temp_file_created = False

        if isinstance(file_input, UploadFile):
            upload_dir = Path(self.settings.UPLOAD_DIR)
            upload_dir.mkdir(exist_ok=True)
            file_path = upload_dir / f"{Path(file_input.filename).stem}_{os.urandom(4).hex()}{Path(file_input.filename).suffix}"
            filename = file_input.filename
            with open(file_path, "wb") as buffer:
                buffer.write(await file_input.read())
            temp_file_created = True
        else:
            file_path = Path(file_input)
            filename = file_path.name

        try:
            db_document = Document(tenant_id=metadata.get("tenant_id"), original_filename=filename)
            self.db_session.add(db_document)
            await self.db_session.flush()

            text = docx2txt.process(str(file_path))
            if not text or not text.strip():
                raise ValueError(f"'{filename}' 파일에서 텍스트를 추출하지 못했습니다.")

            structured_clauses = self._get_structured_data_from_llm(text)

            if not structured_clauses:
                raise ValueError("LLM이 문서에서 조/항을 구조적으로 분리하지 못했습니다.")

            clauses_to_add_db = []
            chunks_for_vectorstore = []
            for item in structured_clauses:
                clauses_to_add_db.append(Clause(
                    document_id=db_document.id, clause_number=item.get("clause_number"),
                    clause_title=item.get("clause_title"), item_number=item.get("item_number"),
                    content=item.get("content")
                ))
                chunk_metadata = {
                    "document_id": db_document.id, "tenant_id": metadata.get("tenant_id"),
                    "jo_number": item.get("clause_number"), "item_number": item.get("item_number")
                }
                chunks_for_vectorstore.append(
                    LangchainDocument(page_content=item.get("content"), metadata=chunk_metadata))

            self.db_session.add_all(clauses_to_add_db)
            self.vector_store.add_documents(chunks_for_vectorstore)
            await self.db_session.commit()
            logger.info(f"🎉 LLM을 통해 문서 '{filename}'의 모든 조/항({len(clauses_to_add_db)}개)을 성공적으로 인덱싱했습니다.")

        except Exception as e:
            logger.error(f"'{filename}' 처리 중 오류 발생. 롤백을 시도합니다.", exc_info=True)
            await self.db_session.rollback()
            raise
        finally:
            if temp_file_created and file_path.exists():
                os.remove(file_path)

