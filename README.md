# RAG 프로토타입

> 리드미는 클로드로 작성했으나, 실제 코드는 바이브 코딩을 쓰기 이전 시절에 작성했습니다. 요즘엔 이런 프로젝트 금방 만들겠지만요.

> RAG(Retrieval Augmented Generation) 시스템 프로토타입입니다.
> 법률 문서·계약서·자문 데이터를 검색 가능한 지식 베이스로 만들고, LLM이 이를 근거로 답변하도록 합니다.

---

## 목차

- [프로젝트 소개](#프로젝트-소개)
- [주요 기능](#주요-기능)
- [시스템 아키텍처](#시스템-아키텍처)
- [기술 스택](#기술-스택)
- [사전 준비](#사전-준비)
- [설치 방법](#설치-방법)
- [환경 설정](#환경-설정)
- [실행 방법](#실행-방법)
- [API 가이드](#api-가이드)
- [유틸리티 스크립트](#유틸리티-스크립트)
- [디렉토리 구조](#디렉토리-구조)
- [트러블슈팅](#트러블슈팅)
- [로드맵](#로드맵)

---

## 프로젝트 소개

기업 법무팀과 변호사들이 사용하는 법무관리 웹서비스입니다. 매일 쌓이는 계약서, 자문 내역, 법령 자료를 효율적으로 활용하기 위해 본 프로토타입은 다음과 같은 가치를 제공하는 것을 목표로 합니다.

- **즉각적 검색**: 수천 건의 문서에서 질문과 가장 관련 있는 부분을 초 단위로 찾아냅니다.
- **근거 기반 답변**: LLM이 환각(hallucination) 없이 실제 문서를 인용하며 답변합니다.
- **테넌트 분리**: 고객사(테넌트)별로 데이터가 분리 검색되어 정보 격리가 보장됩니다.
- **온프레미스 친화**: Ollama 기반 LLM과 로컬 벡터 DB(Chroma)를 사용해 민감한 법률 데이터를 외부로 보내지 않습니다.

---

## 주요 기능

| 기능 | 설명 |
|------|------|
| 문서 업로드 | PDF, DOCX 파일을 업로드하면 자동으로 청크 분할 → 임베딩 → 저장됩니다. |
| 메타데이터 필터링 | `tenant_id`, `document_type` 기준으로 검색 범위를 좁힐 수 있습니다. |
| 질의응답 | 자연어 질문을 입력하면 관련 문서 청크를 검색해 LLM 답변과 출처를 함께 반환합니다. |
| 배치 인덱싱 | `batch_ingest.py`로 디렉토리 단위 대량 문서를 일괄 인덱싱할 수 있습니다. |
| DB 점검 | `inspect_db.py`로 저장된 청크 수와 샘플 데이터를 확인할 수 있습니다. |
| 다중 파일 업로드 | 한 요청으로 여러 파일을 처리하며, 일부 실패 시 207 Multi-Status로 응답합니다. |

---

## 시스템 아키텍처

```
┌──────────────┐      ┌──────────────────────────────────────┐
│   Client     │      │           FastAPI Server             │
│ (Web / Tool) │────▶ │  ┌────────────┐   ┌───────────────┐  │
└──────────────┘      │  │ /api/upload│   │  /api/query   │  │
                      │  └─────┬──────┘   └──────┬────────┘  │
                      │        │                 │           │
                      │  ┌─────▼────────┐  ┌─────▼────────┐  │
                      │  │IngestService │  │  RAGService  │  │
                      │  └─────┬────────┘  └─────┬────────┘  │
                      │        │                 │           │
                      │        │  ┌──────────────┘           │
                      │        │  │                          │
                      │  ┌─────▼──▼─────┐    ┌────────────┐  │
                      │  │ Embedding    │    │ ChatOllama │  │
                      │  │ (KoSRoBERTa) │    │  (LLM)     │  │
                      │  └─────┬────────┘    └─────▲──────┘  │
                      │        │                   │         │
                      │  ┌─────▼───────────────────┴──────┐  │
                      │  │      ChromaDB (Persistent)     │  │
                      │  └────────────────────────────────┘  │
                      └──────────────────────────────────────┘
```

### 처리 흐름

1. **인덱싱 파이프라인** (`/api/upload`)
   PDF/DOCX 로드 → 텍스트 추출 → `RecursiveCharacterTextSplitter`로 청크 분할 (chunk_size=1000, overlap=200) → ko-sroberta-multitask로 임베딩 → ChromaDB 저장

2. **질의 파이프라인** (`/api/query`)
   사용자 질의 임베딩 → 메타데이터 필터 적용 → 상위 K개 청크 검색 → 프롬프트 조립 → Ollama LLM 답변 생성 → 답변 + 출처 반환

---

## 기술 스택

| 분류 | 기술 | 비고 |
|------|------|------|
| 웹 프레임워크 | FastAPI + Uvicorn | 비동기 HTTP API |
| RAG 오케스트레이션 | LangChain (core, community, ollama, huggingface) | Runnable 체인 사용 |
| 벡터 DB | ChromaDB | Persistent 모드, 추후 Milvus 마이그레이션 고려 |
| 임베딩 모델 | `jhgan/ko-sroberta-multitask` | 한국어 특화 |
| LLM | Ollama (기본 `gemma:2b`) | 로컬 추론, 모델 교체 가능 |
| 문서 로더 | PyPDF, Unstructured | PDF / DOCX 지원 |
| 설정 관리 | pydantic-settings | `.env` 기반 |

---

## 사전 준비

본격적으로 실행하기 전에 아래 두 가지가 켜져 있는지 확인합니다.

1. **Ollama 서비스 실행**

   ```bash
   systemctl status ollama
   # 모델이 없다면 미리 풀
   ollama pull gemma:2b
   ```

2. **포트 점유 확인** (예: 8100을 다른 서비스가 점유 중인지)

   ```bash
   ss -tlpn | grep :8100
   ```

3. **Python 3.10+** 권장 (LangChain 최신 버전 호환성)

4. **외부 스토리지 마운트** — 데이터/DB가 큰 용량을 차지하므로 다른 드라이브로 분리되어 있습니다. (이 부분때문에 특정 장소에서밖에 구동이 안됩니다..)
   - 기본 경로: `/media/dev/a/ragdata/buptle_rag_proto/chroma_db`
   - 환경에 맞게 [환경 설정](#환경-설정)에서 변경하세요.

---

## 설치 방법

```bash
# 1) 저장소 클론
git clone <repository-url>
cd buptle_rag_proto

# 2) 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate          # Linux / macOS
# .venv\Scripts\Activate.ps1       # Windows PowerShell

# 3) 패키지 설치
pip install --upgrade pip
pip install -r requirements.txt
```

> 💡 첫 실행 시 `jhgan/ko-sroberta-multitask` 모델이 자동 다운로드됩니다 (약 400MB).

---

## 환경 설정

`app/config.py`에 기본값이 정의되어 있으며, 프로젝트 루트에 `.env` 파일을 만들어 덮어쓸 수 있습니다.

```env
# .env 예시
EMBEDDING_MODEL=jhgan/ko-sroberta-multitask
OLLAMA_MODEL=gemma:2b

CHROMA_PERSIST_DIR=/media/dev/a/ragdata/buptle_rag_proto/chroma_db
CHROMA_COLLECTION_NAME=buptle_rag_collection

CHUNK_SIZE=1000
CHUNK_OVERLAP=200

UPLOAD_DIR=uploaded_files
```

| 환경 변수 | 기본값 | 설명 |
|-----------|--------|------|
| `EMBEDDING_MODEL` | `jhgan/ko-sroberta-multitask` | HuggingFace 모델 ID |
| `OLLAMA_MODEL` | `gemma:2b` | Ollama에 풀(pull)된 모델 이름 |
| `CHROMA_PERSIST_DIR` | (상단 참조) | 벡터 DB 저장 경로 |
| `CHROMA_COLLECTION_NAME` | `buptle_rag_collection` | 컬렉션명 |
| `CHUNK_SIZE` | `1000` | 청크 글자 수 |
| `CHUNK_OVERLAP` | `200` | 청크 간 중첩 글자 수 |
| `UPLOAD_DIR` | `uploaded_files` | 업로드 임시 디렉토리 (처리 후 삭제) |

---

## 실행 방법

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

서버가 뜨면 다음 경로로 접근할 수 있습니다.

- 루트: <http://localhost:8000/>
- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- 헬스 체크: <http://localhost:8000/health>

---

## API 가이드

### 1. 문서 업로드 — `POST /api/upload`

여러 개의 PDF/DOCX 파일을 한 번에 업로드합니다.

**요청 (curl)**

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "files=@contract_001.pdf" \
  -F "files=@advice_002.docx" \
  -F "tenant_id=client_A" \
  -F "document_type=contract"
```

**응답 예시**

```json
{
  "message": "요청이 처리되었습니다.",
  "processed_files": ["contract_001.pdf", "advice_002.docx"],
  "errors": []
}
```

> 일부 파일만 실패하면 HTTP **207 Multi-Status**가 반환되며, `errors` 배열에 사유가 담깁니다.

---

### 2. 질의응답 — `POST /api/query`

**요청 (curl)**

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "지식재산권 이전 조항에서 주의해야 할 점은?",
    "tenant_id": "client_A",
    "document_type": "contract",
    "top_k": 3
  }'
```

**요청 (Python)**

```python
import requests

resp = requests.post(
    "http://localhost:8000/api/query",
    json={
        "query": "비밀유지 의무는 얼마 동안 유지되나요?",
        "tenant_id": "client_A",
        "top_k": 5,
    },
    timeout=60,
)
print(resp.json()["answer"])
for src in resp.json()["sources"]:
    print("-", src["source"])
```

**응답 예시**

```json
{
  "answer": "제공된 문서에 따르면 비밀유지 의무는 계약 종료 후 5년간 유지됩니다 ...",
  "sources": [
    {
      "source": "uploaded_files/advice_002.docx",
      "content": "2.2 비밀유지 조항\n- 계약 종료 후 5년간 비밀유지 의무 존재 ...",
      "metadata": {
        "tenant_id": "client_A",
        "document_type": "contract",
        "source": "uploaded_files/advice_002.docx"
      },
      "score": null
    }
  ]
}
```

---

## 유틸리티 스크립트

### 배치 인덱싱 — `batch_ingest.py`

대량 문서를 디렉토리 단위로 한 번에 인덱싱합니다.

```bash
# 스크립트 상단의 SOURCE_DOCUMENTS_PATH, BATCH_METADATA 수정 후 실행
python batch_ingest.py
```

- 현재 테스트 안전장치로 **상위 100개 파일만** 처리하도록 제한되어 있습니다.
  더 많은 파일을 처리하려면 `batch_ingest.py:63`의 슬라이싱 라인을 조정하세요.
- 실패한 파일은 콘솔에만 출력되므로, 본격 운영 시에는 로그 파일 저장 로직을 추가하는 것을 권장합니다.

### DB 점검 — `inspect_db.py`

저장된 청크 수와 샘플을 확인합니다.

```bash
# 기본: 5개 샘플 출력
python inspect_db.py

# 샘플 개수 지정
python inspect_db.py -n 20
```

---

## 디렉토리 구조

```
buptle_rag_proto/
├── app/
│   ├── main.py                  # FastAPI 진입점 (CORS, 라우터 등록)
│   ├── config.py                # pydantic-settings 기반 설정
│   ├── dependencies.py          # DI 컨테이너 (lru_cache로 싱글톤화)
│   ├── models/
│   │   └── query.py             # 요청/응답 Pydantic 모델
│   ├── routers/
│   │   ├── upload_router.py     # /api/upload
│   │   └── query_router.py      # /api/query
│   └── services/
│       ├── embedding_service.py # HuggingFace 임베딩 래퍼
│       ├── ingest_service.py    # 로드 → 분할 → 임베딩 → 저장
│       └── rag_service.py       # 검색 + LLM 체인
├── batch_ingest.py              # 대량 인덱싱 스크립트
├── inspect_db.py                # ChromaDB 내용 조회 스크립트
├── test_request.py              # API 동작 확인용 샘플 클라이언트
├── requirements.txt
└── README.md
```

> 📦 **데이터·DB 위치 안내**
> `data/`(원본·처리 문서)와 `db/chroma/`(벡터 DB)는 용량 문제로 외부 드라이브(`/media/dev/a/...`)에 이관되어 있습니다. 경로는 `.env`에서 변경할 수 있습니다.

---

## 트러블슈팅

| 증상 | 원인/해결책 |
|------|--------------|
| `ConnectionError: ollama` | `systemctl status ollama`로 서비스 상태 확인. 모델은 `ollama pull <model>`로 미리 다운로드. |
| 업로드 시 500 에러 | PDF가 스캔본(이미지)일 가능성 — `PyPDFLoader`는 텍스트 PDF만 처리합니다. OCR 전처리가 필요할 수 있습니다. |
| `[오류] 데이터베이스 디렉토리를 찾을 수 없습니다` | `CHROMA_PERSIST_DIR` 경로가 존재하지 않거나 마운트 안 됨. 경로/마운트 상태 확인. |
| 답변 품질이 낮음 | `top_k` 늘려보기, `CHUNK_SIZE`/`OVERLAP` 튜닝, 더 큰 LLM(`gemma:7b`, `llama3` 등)으로 교체. |
| `_internal_` 에러 또는 metadata 필터 미작동 | 동일 키로 인덱싱된 문서가 있는지 `inspect_db.py`로 확인. |

---

## 로드맵

- [ ] OCR 파이프라인 추가 (스캔 PDF 대응)
- [ ] 메타데이터 스키마 정형화 (계약일, 당사자, 관할법 등 필드 추가)
- [ ] 하이브리드 검색 (벡터 + BM25)
- [ ] 답변에 인용 인덱스(`[1]`, `[2]`) 자동 부여
- [ ] Milvus 마이그레이션 (대규모 인덱스 대응)
- [ ] 인증/인가 (테넌트별 API Key)
- [ ] 배치 인덱싱 실패 케이스 영구 로깅 및 재시도 큐
- [ ] 평가용 골든 데이터셋 구축 및 회귀 테스트

---

## 운영 체크리스트

서비스 시작 전 아래 항목이 모두 OK인지 확인하세요.

- [ ] `systemctl status ollama` → **active (running)**
- [ ] `ss -tlpn | grep :8100` → 사용 포트 정상
- [ ] `CHROMA_PERSIST_DIR` 마운트 디스크 여유 용량 확인
- [ ] `python inspect_db.py` → 컬렉션 정상 로드
- [ ] `curl http://localhost:8000/health` → `{"status":"healthy"}`
