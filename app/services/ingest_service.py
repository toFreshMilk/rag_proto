# app/services/ingest_service.py

import os
import docx2txt
import re
from pathlib import Path
from typing import Dict, Union
import logging
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.documents import Document as LangchainDocument
from langchain_postgres.vectorstores import PGVector

from app.config import Settings
from app.models.clause import Document, Clause

logger = logging.getLogger(__name__)


class IngestService:
    def __init__(self, db_session: AsyncSession, settings: Settings, vector_store: PGVector):
        self.db_session = db_session
        self.settings = settings
        self.vector_store = vector_store

    def _split_document_into_clauses(self, text: str) -> list[dict]:
        """
        문서 텍스트를 '조' 단위로 나눈 후, 각 '조'를 다시 '항' 단위로 분할합니다.
        - 지적 사항 1: '항'(①, 1. 등)을 분리합니다.
        - 지적 사항 2: content에서 '제X조 제목' 부분을 제거합니다.
        """
        final_clauses = []

        # 1. '제 O조'를 기준으로 문서 전체를 블록으로 분할
        article_pattern = re.compile(r"^(?=제\s*\d+\s*조)", re.MULTILINE)
        article_blocks = article_pattern.split(text)

        for block in article_blocks[1:]:  # 첫 번째 블록은 서문이므로 제외
            if not block.strip():
                continue

            lines = block.strip().split('\n')
            first_line = lines[0].strip()

            # 조 번호와 제목 추출
            title_pattern = re.match(r"제\s*(\d+)\s*조(?:\s*\((.*?)\))?\s*(.*)", first_line)
            jo_num_str, jo_title = "", ""
            if title_pattern:
                jo_num_str = title_pattern.group(1)
                jo_title = (title_pattern.group(2) or title_pattern.group(3) or "").strip()

            if not jo_num_str:
                continue

            # 조 제목 라인을 제외한 나머지 내용
            content_body = '\n'.join(lines[1:]).strip()

            # 2. '항'을 기준으로 나머지 내용을 다시 분할 (①, 1., (1) 등 다양한 형식 지원)
            # '항' 마커로 시작하는 라인을 찾되, 해당 마커는 분리 후에도 유지(Positive Lookahead)
            item_pattern = re.compile(r"^(?=\s*(?:[①-⑳]|\d+\.|\(\d+\)|[가-힣]\.))\s*", re.MULTILINE)
            item_blocks = item_pattern.split(content_body)

            if len(item_blocks) <= 1:
                # '항'이 없는 '조'의 경우, 전체 내용을 하나의 절로 처리
                if content_body:
                    final_clauses.append({
                        "jo_number": f"제{jo_num_str}조",
                        "jo_title": jo_title,
                        "item_number": None,  # 항이 없으므로 Null
                        "content": content_body
                    })
            else:
                # '항'이 있는 경우, 각 '항'을 별도의 절로 처리
                for item_block in item_blocks:
                    if not item_block.strip():
                        continue

                    # '항' 마커와 내용을 분리
                    item_marker_match = re.match(r"^\s*((?:[①-⑳]|\d+\.|\(\d+\)|[가-힣]\.))\s*(.*)", item_block.strip(),
                                                 re.DOTALL)
                    item_num = item_block.strip().split('\n')[0].strip()  # 기본값
                    item_content = item_block.strip()

                    if item_marker_match:
                        item_num = item_marker_match.group(1).strip()
                        # 내용에서 첫 줄의 마커 부분을 제거
                        item_content = item_marker_match.group(2).strip()

                    final_clauses.append({
                        "jo_number": f"제{jo_num_str}조",
                        "jo_title": jo_title,
                        "item_number": item_num,
                        "content": item_content
                    })

        logger.info(f"문서 분할 완료. 총 {len(final_clauses)}개의 조/항 생성.")
        return final_clauses

    async def ingest_file(self, file_input: Union[UploadFile, str, Path], metadata: Dict):
        # (파일 처리 앞부분은 이전과 동일)
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
            # DB에 Document 메타데이터 저장
            db_document = Document(tenant_id=metadata.get("tenant_id"), original_filename=filename)
            self.db_session.add(db_document)
            await self.db_session.flush()

            # 텍스트 추출
            text = docx2txt.process(str(file_path))
            if not text or not text.strip():
                raise ValueError(f"'{filename}' 파일에서 텍스트를 추출하지 못했습니다.")

            # --- ✨✨✨ 개선된 로직 사용 ✨✨✨ ---
            structured_clauses = self._split_document_into_clauses(text)
            if not structured_clauses:
                raise ValueError("문서에서 조/항을 구조적으로 분리하지 못했습니다.")

            clauses_to_add_db = []
            chunks_for_vectorstore = []
            for item in structured_clauses:
                # RDB 저장용 Clause 객체 (item_number 포함)
                clauses_to_add_db.append(Clause(
                    document_id=db_document.id,
                    clause_number=item["jo_number"],
                    clause_title=item["jo_title"],
                    item_number=item["item_number"],  # 신규 필드
                    content=item["content"]
                ))
                # VectorDB 저장용 Langchain Document 객체 (메타데이터에 item_number 추가)
                chunk_metadata = {
                    "document_id": db_document.id,
                    "tenant_id": metadata.get("tenant_id"),
                    "jo_number": item["jo_number"],
                    "item_number": item["item_number"]
                }
                chunks_for_vectorstore.append(LangchainDocument(
                    page_content=item["content"],
                    metadata=chunk_metadata
                ))

            # DB 및 VectorStore에 저장
            self.db_session.add_all(clauses_to_add_db)
            self.vector_store.add_documents(chunks_for_vectorstore)
            await self.db_session.commit()
            logger.info(f"🎉 문서 '{filename}'의 모든 조/항({len(clauses_to_add_db)}개)을 성공적으로 인덱싱했습니다.")

        except Exception as e:
            logger.error(f"'{filename}' 처리 중 오류 발생. 롤백을 시도합니다.", exc_info=True)
            await self.db_session.rollback()
            raise
        finally:
            if temp_file_created and file_path.exists():
                os.remove(file_path)
