import re
import uuid
from typing import List, Dict, Any, Optional
from app.models.document import Document, DocumentChunk


class TextSplitter:
    """문서를 작은 청크로 분할하는 유틸리티 클래스"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """초기화

        Args:
            chunk_size: 각 청크의 최대 문자 수
            chunk_overlap: 청크 간 중복되는 문자 수
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_by_character(self, text: str) -> List[str]:
        """텍스트를 문자 단위로 분할"""
        chunks = []
        current_idx = 0
        text_len = len(text)

        while current_idx < text_len:
            # 청크 끝 위치 계산
            end_idx = min(current_idx + self.chunk_size, text_len)

            # 현재 청크 추출
            chunk = text[current_idx:end_idx]
            chunks.append(chunk)

            # 다음 시작 위치 계산 (중복 고려)
            current_idx = end_idx - self.chunk_overlap
            if current_idx >= text_len:
                break

            # 중복으로 인해 이전과 동일한 청크가 생성되는 경우 방지
            if current_idx <= 0:
                current_idx = end_idx

        return chunks

    def split_by_sentence(self, text: str) -> List[str]:
        """텍스트를 문장 단위로 분할"""
        # 한국어 문장 종결 패턴
        sentence_endings = r'[.!?\n]'

        # 문장 분리
        sentences = re.split(f'({sentence_endings})', text)

        # 문장과 구분자를 다시 합침
        actual_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                actual_sentences.append(sentences[i] + sentences[i + 1])
            else:
                actual_sentences.append(sentences[i])

        # 마지막 요소 처리
        if len(sentences) % 2 == 1:
            actual_sentences.append(sentences[-1])

        # 청크로 조합
        chunks = []
        current_chunk = ""

        for sentence in actual_sentences:
            # 빈 문장 무시
            if not sentence.strip():
                continue

            # 현재 청크에 문장 추가 시 청크 크기 초과 여부 확인
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                chunks.append(current_chunk)
                # 중복을 위해 마지막 문장을 포함하되, 청크 크기를 초과하지 않도록 함
                overlap_sentences = []
                overlap_size = 0
                for s in reversed(current_chunk.split(re.compile(f'(?<={sentence_endings})\s*'))):
                    if overlap_size + len(s) <= self.chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_size += len(s)
                    else:
                        break
                current_chunk = ''.join(overlap_sentences)

            current_chunk += sentence

        # 마지막 청크 추가
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def split_document(self, document: Document) -> List[DocumentChunk]:
        """문서를 청크로 분할"""
        chunks = self.split_by_sentence(document.content)

        document_chunks = []
        for i, chunk_text in enumerate(chunks):
            # 고유 ID 생성
            chunk_id = f"{document.id if document.id else str(uuid.uuid4())}_chunk_{i}"

            # 청크별 메타데이터 생성
            chunk_metadata = {
                **document.metadata,  # 기존 문서 메타데이터 복사
                "chunk_index": i,
                "chunk_count": len(chunks),
                "parent_document_id": document.id if document.id else None
            }

            # DocumentChunk 객체 생성
            document_chunk = DocumentChunk(
                id=chunk_id,
                text=chunk_text,
                metadata=chunk_metadata
            )

            document_chunks.append(document_chunk)

        return document_chunks
