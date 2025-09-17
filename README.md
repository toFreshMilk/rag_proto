# 법틀비즈 RAG 프로토타입 (BuptleBiz RAG Prototype)

법무관리 웹서비스 '법틀비즈'에 AI 기능을 추가하기 위한 RAG(Retrieval Augmented Generation) 시스템 프로토타입입니다.

## 개요

이 프로토타입은 법틀비즈가 가지고 있는 법률 문서, 계약서, 자문 데이터 등을 활용하여 사용자 질의에 적절한 정보를 검색하고 제공하는 시스템입니다. 
FastAPI 기반의 HTTP 엔드포인트를 제공하며, 임베딩 모델로는 `ko-sroberta-multitask`를 사용합니다.

## 설치 방법

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate

# 필요 패키지 설치
pip install -r requirements.txt
```

## 실행 방법

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 시스템 구성

- FastAPI: HTTP 엔드포인트 제공
- ChromaDB: 벡터 데이터베이스 (추후 Milvus로 마이그레이션 가능)
- ko-sroberta-multitask: 임베딩 모델
- LangChain: RAG 파이프라인 구성

## API 엔드포인트

- `POST /api/upload`: 문서 업로드 및 인덱싱
- `POST /api/query`: 질의에 대한 응답 생성

## 디렉토리 구조

```
buptle_rag_proto/
├── app/
│   ├── main.py          # FastAPI 애플리케이션
│   ├── models/          # 데이터 모델
│   ├── services/        # 비즈니스 로직
│   ├── utils/           # 유틸리티 함수
│   └── config.py        # 설정 파일
├── data/                # 저장된 데이터
│   ├── raw/             # 원본 문서
│   └── processed/       # 처리된 문서
├── db/                  # 데이터베이스 관련
│   └── chroma/          # ChromaDB 저장소
├── tests/               # 테스트 코드
├── README.md            # 프로젝트 설명
└── requirements.txt     # 필요 패키지
```
