# /home/dev/buptle_rag_proto/inspect_db.py

import os
import sys
import pprint
import argparse  # 커맨드라인 인자 처리를 위한 라이브러리

# --- 경로 설정 ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

try:
    import chromadb
    from app.config import get_settings
except ImportError as e:
    print(f"[오류] 필요한 모듈을 찾을 수 없습니다: {e}")
    print("이 스크립트는 프로젝트의 가상 환경(.venv)을 활성화한 후 실행해야 합니다.")
    print("예: source .venv/bin/activate")
    sys.exit(1)


def inspect_chromadb(num_samples: int):
    """ChromaDB의 내용을 조회하는 스크립트"""
    settings = get_settings()
    db_path = settings.CHROMA_PERSIST_DIR
    collection_name = settings.CHROMA_COLLECTION_NAME

    print(f"'{db_path}' 경로에서 데이터베이스를 로드합니다...")

    if not os.path.isdir(db_path):
        print(f"\n[오류] 데이터베이스 디렉토리 '{db_path}'를 찾을 수 없습니다.")
        print("먼저 문서를 업로드하여 데이터베이스를 생성해주세요.")
        return

    try:
        client = chromadb.PersistentClient(path=db_path)
        print(f"'{collection_name}' 컬렉션을 조회합니다.")
        collection = client.get_collection(name=collection_name)

        count = collection.count()
        if count == 0:
            print("\n>> 컬렉션에 저장된 데이터가 없습니다.")
            return

        print(f"\n>> 총 {count}개의 데이터 청크가 저장되어 있습니다.")

        # 사용자가 요청한 수만큼 데이터를 가져옵니다.
        results = collection.get(
            limit=num_samples,
            include=["metadatas", "documents"]
        )

        print(f"\n--- 저장된 데이터 샘플 (상위 {len(results['ids'])}개) ---")
        for i in range(len(results['ids'])):
            print(f"\n[문서 ID: {results['ids'][i]}]")
            print("  - Metadata:")
            pprint.pprint(results['metadatas'][i], indent=4, width=120)
            print("  - Document (내용 일부):")
            document_text = results['documents'][i]
            print(f"    '{document_text[:200].replace(chr(10), ' ')}...'")

    except ValueError as e:
        print(f"\n[오류] 컬렉션 '{collection_name}'을(를) 찾을 수 없습니다: {e}")
        print("컬렉션 이름이 config.py 파일과 일치하는지 확인해주세요.")
    except Exception as e:
        print(f"\n[오류] 데이터베이스 조회 중 예상치 못한 오류가 발생했습니다: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ChromaDB 데이터베이스 내용을 조회합니다.")
    parser.add_argument("-n", "--num_samples", type=int, default=5, help="출력할 샘플 데이터의 수")
    args = parser.parse_args()

    inspect_chromadb(args.num_samples)
