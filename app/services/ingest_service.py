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
        문서 텍스트를 서문, 조, 항, 호, 목 단위로 지능적으로 분할합니다.
        1. 조 번호는 숫자만 저장합니다.
        2. 항/호/목 마커가 없는 단락은 순서에 따라 자동으로 번호를 부여합니다.
        3. 서문은 조 번호를 '0'으로 지정합니다.
        """
        final_clauses = []

        # '조' 패턴: 제1조, 제 1조, 제1 조, 제 1 조 (괄호 포함 가능)
        article_pattern = re.compile(r"^(?=제\s*\d+\s*조)", re.MULTILINE)
        blocks = article_pattern.split(text, 1)

        # 1. 서문 처리
        preamble_text = blocks[0].strip()
        if preamble_text:
            preamble_lines = preamble_text.split('\n')
            preamble_title = preamble_lines[0].strip()
            preamble_content = '\n'.join(line for line in preamble_lines[1:] if line.strip()).strip()
            if preamble_content:
                final_clauses.append({
                    "jo_number": "0",  # 요구사항 3: 서문은 0으로
                    "jo_title": preamble_title,
                    "item_number": "1",  # 서문은 하나의 항으로 간주
                    "content": preamble_content
                })

        if len(blocks) < 2:
            return final_clauses

        # 2. 모든 '조' 블록 처리
        remaining_text = blocks[1]
        article_blocks = article_pattern.split(remaining_text)

        for block in article_blocks:
            if not block.strip():
                continue

            lines = block.strip().split('\n')
            first_line = lines[0].strip()

            # 조 번호와 제목 추출
            title_match = re.match(r"제\s*(\d+)\s*조\s*(?:\((.*?)\))?\s*(.*)|(제\d+조)\[(.*?)\]", first_line)
            if not title_match: continue

            jo_num = ""
            jo_title = ""
            if title_match.group(1):  # "제 1조 (제목)"
                jo_num = title_match.group(1)
                jo_title = (title_match.group(2) or title_match.group(3) or "").strip()
            elif title_match.group(4):  # "제7조[제목]"
                jo_num = re.search(r'\d+', title_match.group(4)).group()
                jo_title = title_match.group(5).strip()

            content_body = '\n'.join(lines[1:]).strip()

            # 3. '항/호/목' 단위로 분할 또는 자동 번호 부여
            item_pattern = re.compile(r"^(?=\s*(?:[가-힣]\.|\d+\.|\([가-힣]\)|\(\d+\)|[①-⑳]))", re.MULTILINE)

            # '항' 마커가 하나라도 있는지 확인
            has_explicit_items = item_pattern.search(content_body)

            if has_explicit_items:
                # 명시적 마커가 있으면, 이전 로직과 유사하게 처리
                item_blocks = item_pattern.split(content_body)

                # 마커 시작 전 내용 처리
                if item_blocks[0].strip():
                    final_clauses.append({
                        "jo_number": jo_num,  # 요구사항 1: 숫자만 저장
                        "jo_title": jo_title,
                        "item_number": "1",  # 첫 단락은 1항으로 자동 부여
                        "content": item_blocks[0].strip()
                    })

                for item_block in item_blocks[1:]:
                    if not item_block.strip(): continue

                    marker_match = re.match(r"^\s*([①-⑳]|\d+\.|\(\d+\)|[가-힣]\.|\([가-힣]\))\s*(.*(?:\n|$))((?:.|\n)*)",
                                            item_block)
                    if marker_match:
                        item_num = marker_match.group(1).strip()
                        content = (marker_match.group(2) + marker_match.group(3)).strip()
                        final_clauses.append({
                            "jo_number": jo_num,
                            "jo_title": jo_title,
                            "item_number": item_num,
                            "content": content
                        })

            else:
                # 요구사항 2: 명시적 마커가 없으면, 빈 줄을 기준으로 단락을 나누고 자동 번호 부여
                # 연속된 두 개 이상의 개행 문자를 분리 기준으로 사용
                paragraphs = re.split(r'\n\s*\n', content_body)
                item_counter = 1
                for para in paragraphs:
                    if para.strip():
                        final_clauses.append({
                            "jo_number": jo_num,
                            "jo_title": jo_title,
                            "item_number": str(item_counter),  # 자동 번호 부여
                            "content": para.strip()
                        })
                        item_counter += 1

        logger.info(f"문서 분할 완료. 총 {len(final_clauses)}개의 조/항/호/목 생성.")
        return final_clauses

    async def ingest_file(self, file_input: Union[UploadFile, str, Path], metadata: Dict):
        # (이하 로직은 이전과 동일하므로 생략)
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

            structured_clauses = self._split_document_into_clauses(text)
            if not structured_clauses:
                raise ValueError("문서에서 조/항을 구조적으로 분리하지 못했습니다.")

            clauses_to_add_db = []
            chunks_for_vectorstore = []
            for item in structured_clauses:
                clauses_to_add_db.append(Clause(
                    document_id=db_document.id,
                    clause_number=item["jo_number"],
                    clause_title=item["jo_title"],
                    item_number=item["item_number"],
                    content=item["content"]
                ))
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
