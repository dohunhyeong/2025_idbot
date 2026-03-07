# Busan CIDC RAG Chatbot Backend

FastAPI 기반 Retrieval-Augmented Generation (RAG) 백엔드 서버\
(FastAPIベース Retrieval-Augmented Generation（RAG）バックエンドサーバ)

이 시스템은 법정 감염병 정보를 안내하는 챗봇의 백엔드이며 사용자 질문을
분석하여 벡터 검색과 LLM을 이용해 답변을 생성한다.\
(本システムは法定感染症情報を案内するチャットボットのバックエンドであり、ユーザーの質問を解析してベクトル検索とLLMを利用して回答を生成する。)

------------------------------------------------------------------------

# System Overview (시스템 개요 / システム概要)

주요 기능\
(主な機能)

-   감염병 질의 응답 (感染症質問応答)
-   질병 동의어 정규화 (疾病シノニム正規化)
-   감염병 급수 질문 처리 (感染症等級質問処理)
-   Intent 질문 처리 (인사 / 챗봇 정보)
    (Intent質問処理：挨拶・チャットボット情報)
-   Multi Vector Store Retrieval (マルチベクトルストア検索)
-   LLM 기반 Answer Generation (LLMベース回答生成)
-   MongoDB Query Logging (MongoDBログ保存)
-   React Frontend API 제공 (ReactフロントエンドAPI提供)

------------------------------------------------------------------------

# Architecture Diagram (아키텍처 다이어그램 / アーキテクチャ図)

``` mermaid
flowchart TD

User[User Question] --> API[FastAPI API /query]

API --> InputService
InputService --> IntentService

IntentService -->|Greeting / Meta| IntentResponse[Return Intent Response]

IntentService -->|Disease Question| NormalizationService

NormalizationService --> GradeService

GradeService -->|Grade Question| GradeResponse[Return Grade Answer]

GradeService -->|Normal Disease Query| RoutingService

RoutingService --> RetrieverLoader

RetrieverLoader --> MultiRetriever

MultiRetriever --> CommonRetriever
MultiRetriever --> RespiratoryRetriever
MultiRetriever --> ZoonoticRetriever
MultiRetriever --> WaterFoodRetriever
MultiRetriever --> SexualBloodRetriever
MultiRetriever --> TickRetriever
MultiRetriever --> VaccineRetriever
MultiRetriever --> HealthcareRetriever
MultiRetriever --> TbRetriever

CommonRetriever --> RetrievalResults
RespiratoryRetriever --> RetrievalResults
ZoonoticRetriever --> RetrievalResults
WaterFoodRetriever --> RetrievalResults
SexualBloodRetriever --> RetrievalResults
TickRetriever --> RetrievalResults
VaccineRetriever --> RetrievalResults
HealthcareRetriever --> RetrievalResults
TbRetriever --> RetrievalResults

RetrievalResults --> Aggregator
Aggregator --> Summarizer
Summarizer --> SourceService

SourceService --> FinalAnswer[Final Answer]

FinalAnswer --> MongoDB[(MongoDB Logging)]
```

------------------------------------------------------------------------

# System Architecture (전체 시스템 구조 / システム構成)

``` mermaid
flowchart LR

React[React Frontend] --> FastAPI[FastAPI Backend]
FastAPI --> Pipeline[RAG Pipeline]
Pipeline --> Retrieval[Retriever Layer]
Retrieval --> VectorDB[(FAISS Vector Store)]
Pipeline --> LLM[LLM Answer Generation]
Pipeline --> Mongo[(MongoDB Logging)]
```

------------------------------------------------------------------------

# Project Structure (프로젝트 구조 / プロジェクト構造)

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
    │   ├ common.py
    │   ├ respiratory.py
    │   ├ zoonotic.py
    │   ├ water_food.py
    │   ├ sexual_blood.py
    │   ├ tick.py
    │   ├ vaccine.py
    │   ├ healthcare.py
    │   └ tb.py
    │
    ├ infra
    │ └ mongodb
    │   ├ mongo_client.py
    │   └ query_log_repository.py
    │
    └ resources
      ├ metadata
      │ └ disease_metadata.csv
      └ vectorstore

------------------------------------------------------------------------

# API Endpoints (API 엔드포인트 / APIエンドポイント)

## Query API

POST /query

Request (요청 / リクエスト)

``` json
{
  "query": "탄저의 예방 방법은?"
}
```

Response (응답 / レスポンス)

``` json
{
  "query_id": "...",
  "mongo_id": "...",
  "normalized_query": "탄저의 예방 방법은?",
  "retrievers_used": ["common","bioterror"],
  "latency_ms": 1800,
  "answer": "..."
}
```

------------------------------------------------------------------------

# Admin APIs (관리자 API / 管理者API)

로그 조회\
(ログ取得)

GET /admin/logs

로그 검색\
(ログ検索)

GET /admin/logs/search?q=탄저

로그 상세 조회\
(ログ詳細取得)

GET /admin/logs/{mongo_id}

------------------------------------------------------------------------

# Environment Variables (환경 변수 / 環境変数)

.env example

    MONGODB_URI=mongodb://localhost:27017
    MONGODB_DB=openai
    MONGODB_COLLECTION=2026cidc

    ADMIN_TOKEN=your_admin_token

------------------------------------------------------------------------

# Running the Server (서버 실행 / サーバー実行)

설치 (インストール)

    poetry install

실행 (実行)

    poetry run uvicorn main:app --reload

서버 주소 (サーバーURL)

    http://localhost:8000

------------------------------------------------------------------------

# Frontend (프론트엔드 / フロントエンド)

Frontend는 별도의 React 프로젝트에서 제공된다.\
(フロントエンドは別のReactプロジェクトとして提供される)

Busan Chatbot Frontend

기술 스택 (技術スタック)

-   React 19
-   Vite
-   React Router
-   React Markdown

Frontend URL

    http://localhost:5173

Backend API

    http://localhost:8000

------------------------------------------------------------------------

# Authors (개발자 / 開発者)

Developed for Busan Infectious Disease Management Support Unit.\
(釜山感染症管理支援団向けに開発)

Developers (開発者)

-   Jinbum Joo
-   Hyeong Dohoon

Digital Smart Busan Academy\
Pukyong National University
