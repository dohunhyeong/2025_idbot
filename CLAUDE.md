# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## Project Overview

FastAPI-based RAG (Retrieval-Augmented Generation) backend for the Busan Infectious Disease Management Support Unit (CIDC). Answers Korean-language questions about legally-notifiable infectious diseases using FAISS vector search + Ollama LLM.

## Commands

```bash
# Install dependencies
poetry install

# Run development server
poetry run uvicorn main:app --reload

# Run with Docker
docker-compose up

# Batch evaluation
poetry run python run_batch_trace.py
```

Server: `http://localhost:8000`
Frontend (separate React project): `http://localhost:5173`

## Environment Variables

Copy `.env` with:
```
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=openai
MONGODB_COLLECTION=2026cidc
ADMIN_TOKEN=your_admin_token
LANGFUSE_SECRET_KEY=...
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_HOST=...
```

## Architecture

### RAG Pipeline (3-stage Modular RAG)

`POST /query` → `RagPipeline.run()` → response

**Pre-Retrieval** (query preprocessing):
1. `IntentService` — classifies as greeting/meta/stats/disease via regex; non-disease queries return immediately without retrieval
2. `NormalizationService` — maps disease synonyms/abbreviations to canonical names using `resources/metadata/disease_metadata.csv`; sets disease grade (1–4급)
3. `GradeService` — if query asks about grade classification, returns immediately without vector search
4. `RoutingService` — determines which of 12 FAISS indices to search based on keywords

**Retrieval** (parallel FAISS search):
- `RetrieverLoader` dynamically loads retriever classes for the routed indices
- 12 domain-specific retrievers (common, bioterror_A/B, respiratory, zoonotic, water_food, sexual_blood, tick, vaccine, healthcare, tb, etc.)
- All inherit from `app/retrievers/base_retriever.py` (FAISS + LangChain prompt chain)
- Parallel execution via `asyncio.gather()`

**Post-Retrieval** (answer generation):
- `AggregatorService` — merges and deduplicates results from multiple retrievers
- `SummarizerService` — synthesizes final answer using Ollama `exaone3.5:latest`
- `SourceService` — appends source URLs
- `LoggingService` — persists full query/response to MongoDB

### Service Initialization (main.py)

All services are instantiated at startup and injected into `RagPipeline`. LLM and embeddings are singleton instances shared across retrievers via `RetrieverLoader`.

### Key Infrastructure

- **LLM**: Ollama `exaone3.5:latest` (via `app/core/llm_service.py`)
- **Embeddings**: Ollama `bge-m3` (via `app/core/embedding_service.py`)
- **Vector stores**: Pre-computed FAISS indices at `resources/vectorstore/<domain>/`
- **MongoDB**: Async via Motor (`infra/mongodb/`), stores every query+response
- **Tracing**: Langfuse integration (`app/core/tracing_service.py`)
- **Admin UI**: Jinja2-rendered dashboard at `/admin` (requires `X-ADMIN-TOKEN` header)

### Adding a New Retriever

1. Create `app/retrievers/<name>.py` inheriting `BaseRetriever`
2. Add FAISS index to `resources/vectorstore/<name>/`
3. Register in `app/services/retriever_loader.py`
4. Add routing keywords in `app/services/routing_service.py`
5. Add disease metadata rows to `resources/metadata/disease_metadata.csv`
