# 법정 감염병 상담 RAG 챗봇

부산광역시 감염병관리지원단을 위한 법정 감염병 전문 상담 시스템입니다.
사용자의 감염병 관련 질문에 대해 RAG(Retrieval-Augmented Generation) 파이프라인을 통해 신뢰성 있는 답변을 제공합니다.

---

## 목차

- [주요 기능](#주요-기능)
- [기술 스택](#기술-스택)
- [프로젝트 구조](#프로젝트-구조)
- [시작하기](#시작하기)
- [환경 변수](#환경-변수)
- [API 명세](#api-명세)
- [파이프라인 흐름](#파이프라인-흐름)
- [Retriever 목록](#retriever-목록)
- [어드민 패널](#어드민-패널)
- [새 Retriever 추가 방법](#새-retriever-추가-방법)
- [알려진 이슈](#알려진-이슈)

---

## 주요 기능

- **질의 정규화** — 131개 법정 감염병에 대한 동의어 사전(`disease_metadata.csv`)을 기반으로 질문 내 질병명을 표준 명칭으로 변환
- **전문 Retriever 라우팅** — 질문 내 키워드를 분석해 해당 감염병 분류의 FAISS 벡터스토어로 자동 라우팅
- **FAISS 유사도 검색** — 분류별 전문 인덱스에서 상위 k=3 문서를 검색
- **LLM 기반 최종 요약** — 검색된 컨텍스트를 기반으로 한국어 답변 생성 (컨텍스트 내 정보만 활용)
- **MongoDB 로그 저장** — 모든 질의·응답·지연시간을 Retriever별 컨텍스트와 함께 영구 보관
- **관리자 패널** — 로그 조회·검색 API 제공

---

## 기술 스택

| 구분 | 사용 기술 |
|------|-----------|
| 언어 | Python 3.11+ |
| 웹 프레임워크 | FastAPI + Uvicorn |
| 패키지 관리 | Poetry |
| LLM | Ollama (`exaone3.5:7.8b`) |
| 임베딩 모델 | Ollama (`bge-m3`) |
| 벡터 DB | FAISS (파일 기반) |
| 로그 DB | MongoDB (Motor — 비동기) |
| 프론트엔드 | Vanilla JS + marked.js |

---

## 프로젝트 구조

```
.
├── main.py                         # FastAPI 엔트리포인트 (현재 활성)
├── app/
│   ├── api/
│   │   └── admin_router.py         # 어드민 API (/admin)
│   ├── core/
│   │   ├── llm_service.py          # ChatOllama 싱글톤
│   │   └── embedding_service.py    # OllamaEmbeddings 싱글톤
│   ├── models/
│   │   └── query.py                # Query 데이터 모델
│   ├── pipeline/
│   │   └── pipeline.py             # RagPipeline 클래스 (신규 설계, 미연동)
│   ├── retrievers/
│   │   ├── base_retriever.py       # BaseRetriever (FAISS 로드, 체인 구성)
│   │   ├── common.py               # 공통 Retriever (항상 포함)
│   │   ├── respiratory.py          # 호흡기 감염병
│   │   ├── water_food.py           # 수인성·식품매개 감염병
│   │   ├── sexual_blood.py         # 성매개·혈액매개 감염병
│   │   ├── zoonotic.py             # 인수공통 감염병
│   │   ├── tick.py                 # 기생충·진드기매개 감염병
│   │   ├── vaccine.py              # 예방접종 대상 감염병
│   │   ├── healthcare.py           # 의료관련 감염병 (항생제 내성)
│   │   ├── bioterror_A.py          # 생물테러 감염병 A군
│   │   ├── bioterror_B.py          # 생물테러 감염병 B군
│   │   ├── etc.py                  # 기타 감염병
│   │   └── tb.py                   # 결핵 (FAISS 인덱스 미구비)
│   └── services/
│       ├── input_service.py        # 입력 검증 및 Query 객체 생성
│       ├── normalization_service.py# 질병명 동의어 정규화
│       ├── routing_service.py      # Retriever 라우팅 결정
│       ├── retriever_loader.py     # 동적 Retriever 클래스 로드
│       ├── aggregator_service.py   # Retriever 결과 병합
│       ├── summarizer_service.py   # LLM 기반 최종 답변 생성
│       ├── grade_service.py        # 감염병 급수 질문 단락 처리
│       └── logging_service.py      # MongoDB 로그 저장
├── infra/
│   └── mongodb/
│       ├── mongo_client.py         # Motor 클라이언트 싱글톤
│       └── query_log_repository.py # 로그 CRUD
├── resources/
│   ├── metadata/
│   │   └── disease_metadata.csv    # 131개 감염병 동의어 사전
│   └── vectorstore/
│       └── {retriever_name}/       # FAISS 인덱스 (index.faiss, index.pkl)
└── web/
    └── templates/
        └── admin.html              # 어드민 UI
```

---

## 시작하기

### 사전 요구사항

- Python 3.11+
- [Poetry](https://python-poetry.org/) 설치
- [Ollama](https://ollama.ai/) 로컬 실행 + 모델 Pull 완료
- MongoDB 접근 가능한 URI

```bash
# Ollama 모델 설치
ollama pull exaone3.5:7.8b
ollama pull bge-m3
```

### 설치 및 실행

```bash
# 의존성 설치
poetry install

# 서버 실행
poetry run uvicorn main:app --reload

# 특정 호스트/포트로 실행
poetry run uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 환경 변수

프로젝트 루트에 `.env` 파일을 생성하세요.

```env
MONGODB_URI=mongodb://localhost:27017   # MongoDB 접속 URI
MONGODB_DB=openai                       # 사용할 DB명 (기본값: openai)
ADMIN_TOKEN=your_secret_token           # 어드민 API 인증 토큰
```

---

## API 명세

### POST /query

감염병 관련 질문을 받아 RAG 파이프라인을 통해 답변을 반환합니다.

**요청**

```json
{
  "query": "콜레라의 잠복기와 증상은 무엇인가요?"
}
```

**응답**

```json
{
  "query_id": "uuid",
  "mongo_id": "mongodb_object_id",
  "raw_query": "콜레라의 잠복기와 증상은 무엇인가요?",
  "normalized_query": "콜레라의 잠복기와 증상은 무엇인가요?",
  "grade": null,
  "retrievers_used": ["common", "water_food"],
  "latency_ms": 3241.5,
  "answer": "콜레라의 잠복기는 수 시간에서 5일이며..."
}
```

### GET /admin

어드민 대시보드 페이지 (인증 불필요)

### GET /admin/logs

최근 질의 로그 목록 조회 (헤더 `X-ADMIN-TOKEN` 필요)

### GET /admin/logs/search?q={검색어}

로그 전문 검색 (헤더 `X-ADMIN-TOKEN` 필요)

### GET /admin/logs/{mongo_id}

특정 질의 로그 상세 조회 (헤더 `X-ADMIN-TOKEN` 필요)

---

## 파이프라인 흐름

```
사용자 질문
    │
    ▼
① InputService       — 입력 검증, Query 객체 생성 (UUID 부여)
    │
    ▼
② NormalizationService — 동의어 사전으로 질병명 표준화
    │
    ▼
③ RoutingService     — 키워드 매칭으로 사용할 Retriever 선택
    │                   (common은 항상 포함)
    ▼
④ RetrieverLoader    — Retriever 클래스 동적 임포트 및 인스턴스 생성
    │
    ▼
⑤ Retriever 실행     — FAISS 검색 → 각 Retriever의 prompt|llm 체인으로 답변 생성
    │
    ▼
⑥ AggregatorService  — 각 Retriever 답변을 마크다운 섹션으로 병합·중복 제거
    │
    ▼
⑦ SummarizerService  — LLM으로 최종 답변 합성 (검색된 컨텍스트 범위 내)
    │
    ▼
⑧ MongoDB 저장       — 질의·답변·컨텍스트·지연시간 영구 보관
    │
    ▼
JSON 응답 반환
```

---

## Retriever 목록

| Retriever | 대상 감염병 분류 | FAISS 인덱스 |
|-----------|----------------|-------------|
| `common` | 공통 (항상 포함) | ✅ |
| `respiratory` | 호흡기 감염병 (인플루엔자, 코로나19 등) | ✅ |
| `water_food` | 수인성·식품매개 감염병 (콜레라, 장티푸스 등) | ✅ |
| `sexual_blood` | 성매개·혈액매개 감염병 (HIV, 매독 등) | ✅ |
| `zoonotic` | 인수공통 감염병 (말라리아, 뎅기열 등) | ✅ |
| `tick` | 기생충·진드기매개 감염병 | ✅ |
| `vaccine` | 예방접종 대상 감염병 (홍역, 수두 등) | ✅ |
| `healthcare` | 의료관련 감염병 (MRSA, CRE 등) | ✅ |
| `bioterror_A` | 생물테러 감염병 A군 (두창, 탄저 등) | ✅ |
| `bioterror_B` | 생물테러 감염병 B군 (SARS, MERS 등) | ✅ |
| `etc` | 기타 감염병 (수족구병, 한센병 등) | ✅ |
| `tb` | 결핵 | ❌ 미구비 |

---

## 어드민 패널

`GET /admin`으로 접속하면 질의 로그를 조회할 수 있는 관리자 페이지가 제공됩니다.
로그 API 호출 시에는 HTTP 헤더에 `X-ADMIN-TOKEN` 값을 포함해야 합니다.

```
X-ADMIN-TOKEN: {ADMIN_TOKEN 환경변수 값}
```

---

## 새 Retriever 추가 방법

1. `app/retrievers/{name}.py` 파일 생성, `{PascalCase}Retriever` 클래스 정의 (`BaseRetriever` 상속)
2. `super().__init__("{name}", llm, embeddings)` 호출 — `{name}`은 FAISS 인덱스 폴더명과 일치해야 함
3. `_build_prompt()` 메서드 구현 — `{context}`, `{question}` 변수를 포함한 `PromptTemplate` 반환
4. `app/services/routing_service.py`의 `routing_rules`에 라우팅 키워드 추가
5. FAISS 인덱스를 `resources/vectorstore/{name}/` 디렉터리에 배치 (`index.faiss`, `index.pkl`)

---

## 알려진 이슈

- **`bioterror_A` / `bioterror_B` 클래스명 불일치** — `RetrieverLoader`는 `BioterrorARetriever` / `BioterrorBRetriever`를 기대하지만, 실제 파일은 `BioterrorRetriever` / `BioterrorRetriever_B`로 정의되어 있습니다. FAISS 폴더 초기화 경로도 수정이 필요합니다.
- **정규화는 첫 번째 매칭에서 중단** — 하나의 질문에 여러 질병명이 포함된 경우 첫 번째만 정규화됩니다.
- **라우팅은 단순 부분 문자열 매칭** — 짧은 키워드가 유사한 질병명에 의도치 않게 매칭될 수 있습니다.
- **`tb` Retriever** — 클래스는 존재하나 FAISS 인덱스(`resources/vectorstore/tb/`)가 없어 동작하지 않습니다.
- **`web/router.py`** — `main.py`에 마운트되지 않은 미사용 코드입니다.
