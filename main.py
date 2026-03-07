# main.py (Mongo 저장 + retriever별 context 저장 + 시간 측정 포함)

import os
import time
import logging
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.input_service import InputService
from app.services.intent_service import IntentService
from app.services.grade_service import GradeService
from app.services.normalization_service import NormalizationService
from app.services.routing_service import RoutingService
from app.services.retriever_loader import RetrieverLoader
from app.services.aggregator_service import AggregatorService
from app.services.summarizer_service import SummarizerService
from app.services.logging_service import LoggingService
from app.services.source_service import SourceService

from app.core.llm_service import LLMService
from app.core.embedding_service import EmbeddingService

from infra.mongodb.mongo_client import MongoClientProvider
from infra.mongodb.query_log_repository import QueryLogRepository

from app.api.admin_router import router as admin_router

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router)

logger = logging.getLogger("uvicorn.error")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    logger.error(f"[422] url={request.url} body={body.decode('utf-8', 'ignore')}")
    logger.error(f"[422] errors={exc.errors()}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


llm = LLMService().get_llm()
embeddings = EmbeddingService().get_embeddings()

input_service = InputService()
intent_service = IntentService()
grade_service = GradeService()
normalization_service = NormalizationService()
routing_service = RoutingService()

retriever_loader = RetrieverLoader(llm, embeddings)
aggregator = AggregatorService()
summarizer = SummarizerService(llm)
source_service = SourceService()

mongo_client = MongoClientProvider.get_client()
mongo_db = mongo_client.get_database(os.getenv("MONGODB_DB", "openai"))
query_repo = QueryLogRepository(mongo_db)
logging_service = LoggingService(query_repo)


class QueryInput(BaseModel):
    query: str


@app.post("/query")
async def query_endpoint(query_input: QueryInput):
    start_perf = time.perf_counter()
    query_time = datetime.now(timezone.utc)

    try:
        query_obj = input_service.create_query(query_input.query)

        intent = intent_service.detect_intent(query_obj.raw_text)
        if intent in ["greeting", "meta"]:
            final_answer = intent_service.build_response(intent)

            response_time = datetime.now(timezone.utc)
            latency_ms = round((time.perf_counter() - start_perf) * 1000, 2)

            doc = {
                "query_id": query_obj.id,
                "raw_query": query_obj.raw_text,
                "normalized_query": query_obj.raw_text,
                "grade": None,
                "retrievers_used": [],
                "retriever_results": [],
                "final_answer": final_answer,
                "query_time": query_time,
                "response_time": response_time,
                "latency_ms": latency_ms,
                "mode": "intent_only"
            }

            mongo_id = await logging_service.save(doc)

            return {
                "query_id": query_obj.id,
                "mongo_id": mongo_id,
                "raw_query": query_obj.raw_text,
                "normalized_query": query_obj.raw_text,
                "grade": None,
                "retrievers_used": [],
                "latency_ms": latency_ms,
                "answer": final_answer
            }

        query_obj = normalization_service.normalize_query(query_obj)

        if grade_service.is_grade_question(query_obj.raw_text):
            final_answer = grade_service.build_answer(query_obj)

            response_time = datetime.now(timezone.utc)
            latency_ms = round((time.perf_counter() - start_perf) * 1000, 2)

            doc = {
                "query_id": query_obj.id,
                "raw_query": query_obj.raw_text,
                "normalized_query": query_obj.normalized_text,
                "grade": query_obj.grade,
                "retrievers_used": [],
                "retriever_results": [],
                "final_answer": final_answer,
                "query_time": query_time,
                "response_time": response_time,
                "latency_ms": latency_ms,
                "mode": "grade_only"
            }

            mongo_id = await logging_service.save(doc)

            return {
                "query_id": query_obj.id,
                "mongo_id": mongo_id,
                "raw_query": query_obj.raw_text,
                "normalized_query": query_obj.normalized_text,
                "grade": query_obj.grade,
                "retrievers_used": [],
                "latency_ms": latency_ms,
                "answer": final_answer
            }

        query_obj = routing_service.route_retrievers(query_obj)
        retrievers = retriever_loader.load(query_obj.retrievers)

        retriever_results = []
        common_urls = []

        for name, retriever in zip(query_obj.retrievers, retrievers):
            docs = retriever.retriever.invoke(query_obj.normalized_text)
            context = "\n".join(d.page_content for d in docs)

            if name == "common":
                for doc in docs:
                    url = doc.metadata.get("source_url")
                    if url and url not in common_urls:
                        common_urls.append(url)

            answer = retriever.chain.invoke({
                "context": context,
                "question": query_obj.normalized_text
            })

            retriever_results.append({
                "retriever": name,
                "answer": answer,
                "context": context
            })

        answers_for_merge = [
            (r["retriever"], r["answer"])
            for r in retriever_results
        ]

        aggregated_text = aggregator.aggregate(answers_for_merge)
        final_answer = summarizer.summarize(aggregated_text)

        final_answer = source_service.append_sources(
            final_answer,
            common_urls
        )

        response_time = datetime.now(timezone.utc)
        latency_ms = round((time.perf_counter() - start_perf) * 1000, 2)

        doc = {
            "query_id": query_obj.id,
            "raw_query": query_obj.raw_text,
            "normalized_query": query_obj.normalized_text,
            "grade": query_obj.grade,
            "retrievers_used": query_obj.retrievers,
            "retriever_results": retriever_results,
            "final_answer": final_answer,
            "query_time": query_time,
            "response_time": response_time,
            "latency_ms": latency_ms
        }

        mongo_id = await logging_service.save(doc)

        return {
            "query_id": query_obj.id,
            "mongo_id": mongo_id,
            "raw_query": query_obj.raw_text,
            "normalized_query": query_obj.normalized_text,
            "grade": query_obj.grade,
            "retrievers_used": query_obj.retrievers,
            "latency_ms": latency_ms,
            "answer": final_answer
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))