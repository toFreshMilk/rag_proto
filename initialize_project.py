# scripts/initialize_project.py

import logging
import os
import asyncio

# .env 파일 로드를 가장 먼저 수행
from dotenv import load_dotenv
load_dotenv()

# 필요한 모듈 임포트
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text # text 함수 임포트
from app.config import settings
from app.models.base import Base
from langchain_postgres.v2.engine import PGEngine

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    logger.info("=== 프로젝트 데이터베이스 초기화 스크립트 시작 (비동기) ===")
    engine = create_async_engine(settings.DATABASE_URL)

    try:
        async with engine.begin() as conn:
            logger.info("데이터베이스 연결 성공.")

            # --- SQLAlchemy 테이블 생성 (이미 있으면 건너뜀) ---
            logger.info("SQLAlchemy 모델 테이블(documents, clauses)을 생성합니다...")
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)
            logger.info("SQLAlchemy 모델 테이블 생성을 완료했습니다. (이미 존재하면 건너뜀)")

            # --- PGVector 테이블 존재 여부 확인 ---
            logger.info(f"PGVector 컬렉션 테이블 '{settings.PGVECTOR_COLLECTION_NAME}' 존재 여부를 확인합니다...")
            result = await conn.execute(
                text("SELECT to_regclass(:table_name)"),
                {"table_name": f"public.{settings.PGVECTOR_COLLECTION_NAME}"}
            )
            table_exists = result.scalar_one_or_none() is not None

            if not table_exists:
                logger.info("PGVector 컬렉션 테이블이 존재하지 않으므로 새로 생성합니다...")
                pg_engine = PGEngine.from_connection_string(settings.DATABASE_URL)
                await pg_engine.ainit_vectorstore_table(
                    table_name=settings.PGVECTOR_COLLECTION_NAME,
                    vector_size=settings.VECTOR_SIZE,
                )
                logger.info(f"PGVector 컬렉션 테이블 '{settings.PGVECTOR_COLLECTION_NAME}' 생성을 완료했습니다.")
            else:
                logger.info("PGVector 컬렉션 테이블이 이미 존재하므로 생성을 건너뜁니다.")

        logger.info("🎉 모든 초기화 작업이 성공적으로 완료되었습니다.")

    except Exception as e:
        logger.critical(f"초기화 중 심각한 오류 발생: {e}", exc_info=True)
        logger.critical("`.env` 파일, DB 서버 상태, `vector` 확장 설치 여부를 확인해주세요.")
        exit(1)
    finally:
        await engine.dispose()
        logger.info("데이터베이스 엔진 연결을 해제했습니다.")


if __name__ == "__main__":
    # 비동기 main 함수 실행
    asyncio.run(main())
