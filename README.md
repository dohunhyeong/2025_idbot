# Busan CIDC RAG Chatbot Backend

FastAPI 기반 Retrieval-Augmented Generation (RAG) 백엔드 서버

이 시스템은 법정 감염병 정보를 안내하는 챗봇의 백엔드이며 사용자 질문을
분석하여 벡터 검색과 LLM을 이용해 답변을 생성한다.

------------------------------------------------------------------------

# System Overview (시스템 개요)

주요 기능

-   감염병 질의 응답
-   질병 동의어 정규화
-   감염병 급수 질문 처리
-   Intent 질문 처리 (인사 / 챗봇 정보 / 감염병 통계)
-   Multi Vector Store Retrieval
-   LLM 기반 Answer Generation
-   MongoDB Query Logging
-   React Frontend API 제공

------------------------------------------------------------------------

# Architecture Diagram (아키텍처 다이어그램)

``` mermaid
flowchart TD

User[User Question] --> API[FastAPI API /query]

API --> InputService
InputService --> IntentService

IntentService -->|Greeting / Meta / Stats| IntentResponse[Return Intent Response]

IntentService -->|Disease Question| NormalizationService

NormalizationService --> GradeService

GradeService -->|Grade Question| GradeResponse[Return Grade Answer]

GradeService -->|Normal Disease Query| RoutingService

RoutingService --> RetrieverLoader

RetrieverLoader --> MultiRetriever

MultiRetriever --> CommonRetriever
MultiRetriever --> BioterrorARetriever
MultiRetriever --> BioterrorBRetriever
MultiRetriever --> RespiratoryRetriever
MultiRetriever --> ZoonoticRetriever
MultiRetriever --> WaterFoodRetriever
MultiRetriever --> SexualBloodRetriever
MultiRetriever --> TickRetriever
MultiRetriever --> VaccineRetriever
MultiRetriever --> HealthcareRetriever
MultiRetriever --> TbRetriever
MultiRetriever --> EtcRetriever

CommonRetriever --> RetrievalResults
BioterrorARetriever --> RetrievalResults
BioterrorBRetriever --> RetrievalResults
RespiratoryRetriever --> RetrievalResults
ZoonoticRetriever --> RetrievalResults
WaterFoodRetriever --> RetrievalResults
SexualBloodRetriever --> RetrievalResults
TickRetriever --> RetrievalResults
VaccineRetriever --> RetrievalResults
HealthcareRetriever --> RetrievalResults
TbRetriever --> RetrievalResults
EtcRetriever --> RetrievalResults

RetrievalResults --> Aggregator
Aggregator --> Summarizer
Summarizer --> SourceService

SourceService --> FinalAnswer[Final Answer]

FinalAnswer --> MongoDB[(MongoDB Logging)]
```

------------------------------------------------------------------------

# System Architecture (전체 시스템 구조)

``` mermaid
flowchart LR

React[React Frontend] --> FastAPI[FastAPI Backend]
FastAPI --> Pipeline[RAG Pipeline]
Pipeline --> Retrieval[Retriever Layer]
Retrieval --> Embedding[Embedding Service]
Embedding --> VectorDB[(FAISS Vector Store)]
Pipeline --> LLM[LLM Answer Generation]
Pipeline --> Mongo[(MongoDB Logging)]
```

------------------------------------------------------------------------

# RAG Architecture (RAG 아키텍처)

이 시스템은 **Advanced RAG / Modular RAG** 구조를 채택한다.
단순히 쿼리를 벡터 검색에 그대로 넘기는 Naive RAG와 달리,
검색 전(Pre-Retrieval) · 검색(Retrieval) · 검색 후(Post-Retrieval) 3단계로 파이프라인이 구성된다.

## Pre-Retrieval

사용자 질문을 벡터 검색에 넘기기 전에 질문의 의도와 형태를 정제한다.

| 구성 요소 | 역할 |
|----------|------|
| IntentService | 질문 유형 분류 (인사 / 챗봇 정보 / 감염병 통계 / 질병 질의). 질병 질의가 아닌 경우 검색 없이 즉시 응답 |
| NormalizationService | disease_metadata.csv 기반 동의어·약칭을 정규 병명으로 변환하고 감염병 급수(1~4급) 설정 |
| GradeService | 급수 관련 질문 감지 시 벡터 검색 없이 즉시 응답 |
| RoutingService | 정규화된 쿼리의 키워드를 분석하여 검색할 Vector Store 목록 결정 |

## Retrieval

도메인별로 분리된 FAISS 인덱스에서 병렬로 검색을 수행한다.

| 구성 요소 | 역할 |
|----------|------|
| RetrieverLoader | 라우팅 결과에 따라 Retriever 클래스를 동적으로 로드 |
| Embedding Service | Ollama bge-m3 모델로 쿼리를 벡터로 변환 |
| FAISS Vector Store | 도메인별 12개 인덱스(common, bioterror_A, bioterror_B, respiratory 등)에서 유사 문서 병렬 검색 |

## Post-Retrieval

여러 Retriever에서 수집된 결과를 정제하고 최종 답변을 생성한다.

| 구성 요소 | 역할 |
|----------|------|
| AggregatorService | 복수 Retriever의 답변 병합 및 중복 제거 |
| SummarizerService | LLM(Ollama exaone3.5:7.8b)으로 병합 결과를 단일 답변으로 재요약 |
| SourceService | 답변에 출처 URL을 추가 |
| LoggingService | 질의·응답 전체를 MongoDB에 저장 |

------------------------------------------------------------------------

# Project Structure (프로젝트 구조)

    backend
    │
    ├ main.py
    │
    ├ app
    │ ├ api
    │ │ └ admin_router.py
    │ │
    │ ├ core
    │ │ ├ llm_service.py
    │ │ └ embedding_service.py
    │ │
    │ ├ models
    │ │ └ query.py
    │ │
    │ ├ pipeline
    │ │ └ pipeline.py
    │ │
    │ ├ services
    │ │ ├ input_service.py
    │ │ ├ intent_service.py
    │ │ ├ grade_service.py
    │ │ ├ normalization_service.py
    │ │ ├ routing_service.py
    │ │ ├ retriever_loader.py
    │ │ ├ aggregator_service.py
    │ │ ├ summarizer_service.py
    │ │ ├ source_service.py
    │ │ └ logging_service.py
    │ │
    │ └ retrievers
    │   ├ base_retriever.py
    │   ├ common.py
    │   ├ bioterror_A.py
    │   ├ bioterror_B.py
    │   ├ respiratory.py
    │   ├ zoonotic.py
    │   ├ water_food.py
    │   ├ sexual_blood.py
    │   ├ tick.py
    │   ├ vaccine.py
    │   ├ healthcare.py
    │   ├ tb.py
    │   └ etc.py
    │
    ├ infra
    │ └ mongodb
    │   ├ mongo_client.py
    │   └ query_log_repository.py
    │
    ├ resources
    │ ├ metadata
    │ │ └ disease_metadata.csv
    │ └ vectorstore
    │
    └ web
      ├ router.py
      └ templates
        └ admin.html

------------------------------------------------------------------------

# API Endpoints (API 엔드포인트)

## Query API

POST /query

Request (요청)

``` json
{
  "query": "탄저의 예방 방법은?"
}
```

Response (응답)

``` json
{
  "query_id": "...",
  "mongo_id": "...",
  "raw_query": "탄저의 예방 방법은?",
  "normalized_query": "탄저의 예방 방법은?",
  "grade": 1,
  "retrievers_used": ["common", "bioterror_A"],
  "latency_ms": 1800,
  "answer": "..."
}
```

------------------------------------------------------------------------

# Admin APIs (관리자 API)

관리자 대시보드

GET /admin

로그 조회

GET /admin/logs

로그 검색

GET /admin/logs/search?q=탄저

로그 상세 조회

GET /admin/logs/{mongo_id}

인증 헤더: `X-ADMIN-TOKEN: your_admin_token`

------------------------------------------------------------------------

# Environment Variables (환경 변수)

.env example

    MONGODB_URI=mongodb://localhost:27017
    MONGODB_DB=openai
    MONGODB_COLLECTION=2026cidc

    ADMIN_TOKEN=your_admin_token

------------------------------------------------------------------------

# Running the Server (서버 실행)

설치

    poetry install

실행

    poetry run uvicorn main:app --reload

서버 주소

    http://localhost:8000

------------------------------------------------------------------------

# Frontend (프론트엔드)

Frontend는 별도의 React 프로젝트에서 제공된다.

Busan Chatbot Frontend

기술 스택

-   React 19
-   Vite
-   React Router
-   React Markdown

Frontend URL

    http://localhost:5173

Backend API

    http://localhost:8000

------------------------------------------------------------------------

# Authors (개발자)

Developed for Busan Infectious Disease Management Support Unit.

Developers

-   Jinbum Joo
-   Hyeong Dohoon

Digital Smart Busan Academy\
Pukyong National University
