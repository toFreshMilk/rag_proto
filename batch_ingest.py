# /home/dev/buptle_rag_proto/batch_ingest.py

import os
import sys
import asyncio
from pathlib import Path
from typing import List, Optional, Dict

# --- 경로 설정 ---
# 이 스크립트 파일의 위치를 기준으로 프로젝트 루트 디렉토리를 계산합니다.
# 이렇게 하면 어떤 경로에서 python batch_ingest.py를 실행해도 항상 올바르게 동작합니다.
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.dependencies import get_ingest_service
from app.services.ingest_service import IngestService

# --- 사용자 설정 ---
# 1. 문서들이 저장된 외부 디렉토리 경로, 추후 환경 변수 처리 해야할 듯. 그리고 테넌트나 문서 종류별로 폴더링 해야함.
SOURCE_DOCUMENTS_PATH = "/media/dev/a/docxs"

# 2. 이 일괄 작업으로 추가되는 모든 문서에 적용할 공통 메타데이터 (선택 사항)
# 특정 테넌트의 데이터를 한 번에 넣는 경우 등에 사용합니다.
BATCH_METADATA: Optional[Dict] = {
    "tenant_id": "client_A",
    "document_type": "contract"
}


# -----------------

class MockUploadFile:
    """FastAPI의 UploadFile 객체를 흉내 내는 클래스"""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.filename = file_path.name

    async def read(self) -> bytes:
        with open(self.file_path, "rb") as f:
            return f.read()


async def main():
    """일괄 문서 인덱싱 작업을 실행하는 메인 함수"""
    source_dir = Path(SOURCE_DOCUMENTS_PATH)
    if not source_dir.is_dir():
        print(f"[오류] 소스 디렉토리를 찾을 수 없습니다: '{SOURCE_DOCUMENTS_PATH}'")
        print("스크립트 상단의 SOURCE_DOCUMENTS_PATH 변수를 올바른 경로로 수정해주세요.")
        return

    # IngestService 인스턴스를 가져옵니다.
    ingest_service: IngestService = get_ingest_service()
    print("문서 처리 서비스가 초기화되었습니다.")

    allowed_extensions = {".docx", ".pdf"}
    all_files: List[Path] = [  # 변수 이름 변경
        p for p in source_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in allowed_extensions
    ]

    # --- 테스트를 위해 100개만 선택 ---
    files_to_process = all_files[:100]
    # ---------------------------------


    if not files_to_process:
        print(f"'{SOURCE_DOCUMENTS_PATH}' 디렉토리에서 처리할 문서를 찾지 못했습니다. (docx, pdf 파일 확인)")
        return

    print(f"총 {len(files_to_process)}개의 문서를 처리합니다...")

    success_count = 0
    error_count = 0

    for i, file_path in enumerate(files_to_process):
        print(f"  ({i + 1}/{len(files_to_process)}) 처리 중: {file_path.name} ... ", end="", flush=True)
        try:
            mock_file = MockUploadFile(file_path)
            await ingest_service.ingest_file(mock_file, BATCH_METADATA)
            print("성공")
            success_count += 1
        except Exception as e:
            print(f"실패. 오류: {e}")
            error_count += 1

    print("\n--- 일괄 처리 완료 ---")
    print(f"성공: {success_count}개")
    print(f"실패: {error_count}개")

    db_path = ingest_service.settings.CHROMA_PERSIST_DIR
    print(f"데이터베이스 '{db_path}'가 '{PROJECT_ROOT}' 폴더 내에 생성/업데이트되었습니다.")


if __name__ == "__main__":
    asyncio.run(main())
# 192.168.1.13
# 실패하는 케이스는 따로 기록하던지 처리해서 분석해야할듯