알겠어. 이번엔 불필요한 말 안 하고, 그냥 네가 바로 긁어서 붙여넣을 수 있게 **완성된 README 마크다운 전체**만 줄게.

---

# 법틀비즈 RAG 프로토타입 (BuptleBiz RAG Prototype)

법무관리 웹서비스 **법틀비즈**에 AI 기능을 추가하기 위한 **RAG (Retrieval Augmented Generation)** 시스템의 프로토타입입니다.
법률 문서, 계약서, 자문 데이터를 활용하여 사용자 질의에 대해 신뢰성 있는 검색 및 응답 생성을 목표로 합니다.

---

## 개요

* **API 서버**: FastAPI
* **데이터베이스**: PostgreSQL (구조화 데이터) + pgvector (벡터 데이터)
* **임베딩 모델**: `jhgan/ko-sroberta-multitask` (HuggingFace)
* **LLM**: Ollama (예: gemma:2b 등 로컬 모델)
* **RAG 파이프라인**: LangChain

---

## 시스템 구성

* **API 서버**: FastAPI
* **데이터베이스**: PostgreSQL + pgvector
* **임베딩 모델**: HuggingFace 기반
* **LLM 서버**: Ollama
* **파이프라인**: LangChain 기반 RAG

---

## 디렉토리 구조

```
buptle_rag_proto/
├── app/
│   ├── main.py          # FastAPI 실행 진입점
│   ├── models/          # SQLAlchemy 모델 정의
│   ├── services/        # 비즈니스 로직 (RAG, 임베딩 등)
│   ├── routers/         # API 라우터
│   ├── utils/           # 유틸 함수
│   ├── database.py      # DB 세션 관리
│   └── config.py        # 설정 파일
├── sample_docs/         # 샘플 문서
├── tests/               # 테스트 코드
├── .env                 # 환경 변수 (DB 접속 정보 등)
├── README.md            # 프로젝트 설명
└── requirements.txt     # 의존성 목록
```

---

## 1. 개발 환경 설정 (최초 1회)

### 1.1 PostgreSQL 설치

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib -y
```

### 1.2 PostgreSQL 서비스 시작

```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo systemctl status postgresql
```

### 1.3 DB 및 사용자 생성

```sql
-- 사용자 생성
CREATE USER buptle_rag_user WITH PASSWORD '1111';

-- 데이터베이스 생성
CREATE DATABASE buptle_rag_db;

-- 권한 부여
GRANT ALL PRIVILEGES ON DATABASE buptle_rag_db TO buptle_rag_user;

-- pgvector 확장 활성화
\c buptle_rag_db
CREATE EXTENSION IF NOT EXISTS vector;
       
-- 1. 'public' 스키마를 사용하고, 그 안에 객체를 생성할 권한 부여
GRANT USAGE, CREATE ON SCHEMA public TO buptle_rag_user;

-- 2. 'public' 스키마 안의 모든 '기존' 테이블에 대한 모든 권한 부여
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO buptle_rag_user;

-- 3. 'public' 스키마 안의 모든 '기존' 시퀀스(SERIAL 등)에 대한 모든 권한 부여
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO buptle_rag_user;

-- 4. 앞으로 생성될 '모든 새로운' 테이블에 대해서도 자동으로 모든 권한 부여
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO buptle_rag_user;

-- 5. 앞으로 생성될 '모든 새로운' 시퀀스에 대해서도 자동으로 모든 권한 부여
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO buptle_rag_user;

       
```

### 1.4 외부 접속 허용

**postgresql.conf 수정**

```text
listen_addresses = '*'
```

**pg_hba.conf 수정**

```text
# TYPE     DATABASE   USER   ADDRESS           METHOD
hostnossl  all        all    192.168.1.0/24    md5
hostssl    all        all    192.168.1.0/24    md5
```

**변경사항 적용**

```bash
sudo systemctl restart postgresql

# postgresql-16-pgvector 형식으로 버전에 맞게 설치
sudo apt install postgresql-16-pgvector

sudo -u postgres psql
CREATE EXTENSION IF NOT EXISTS vector;

```

---

## 2. 프로젝트 실행

### 2.1 Python 환경 준비

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2.2 로컬 LLM 서버 실행 (Ollama)

```bash
systemctl status ollama
```

### 2.3 FastAPI 서버 실행

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8100
```

> 서버 최초 실행 시 필요한 테이블(`documents`, `clauses` 등)이 자동 생성됩니다.

---

## API 엔드포인트

* **POST `/api/upload`** : 문서 업로드 및 인덱싱
* **POST `/api/query`** : 사용자 질의 응답 생성

---
