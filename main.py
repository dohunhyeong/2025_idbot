# main.py (Mongo 저장 + retriever별 context 저장 + 시간 측정 포함)

import os
import time
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.services.input_service import InputService
from app.services.normalization_service import NormalizationService
from app.services.routing_service import RoutingService
from app.services.retriever_loader import RetrieverLoader
from app.services.aggregator_service import AggregatorService
from app.services.summarizer_service import SummarizerService

from app.core.llm_service import LLMService
from app.core.embedding_service import EmbeddingService

from infra.mongodb.mongo_client import MongoClientProvider
from infra.mongodb.query_log_repository import QueryLogRepository
from app.services.logging_service import LoggingService

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging

load_dotenv()

app = FastAPI()
logger = logging.getLogger("uvicorn.error")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    logger.error(f"[422] url={request.url} body={body.decode('utf-8', 'ignore')}")
    logger.error(f"[422] errors={exc.errors()}")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})
# 🔹 전역 싱글톤 (앱 시작 시 1회 생성)
llm = LLMService().get_llm()
embeddings = EmbeddingService().get_embeddings()

input_service = InputService()
normalization_service = NormalizationService()
routing_service = RoutingService()

retriever_loader = RetrieverLoader(llm, embeddings)
aggregator = AggregatorService()
summarizer = SummarizerService(llm)

# 🔹 Mongo (env 기반)
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
        # 1️⃣ Query 객체 생성
        query_obj = input_service.create_query(query_input.query)

        # 2️⃣ 동의어 정규화 + 급수 설정
        query_obj = normalization_service.normalize_query(query_obj)

        # 3️⃣ 라우팅 (사용할 retriever 결정)
        query_obj = routing_service.route_retrievers(query_obj)

        # 4️⃣ Retriever 객체 생성
        retrievers = retriever_loader.load(query_obj.retrievers)

        # 5️⃣ 각 retriever 실행 + retriever별 context 저장
        retriever_results = []

        for name, retriever in zip(query_obj.retrievers, retrievers):
            # docs 뽑아서 context 저장
            docs = retriever.retriever.invoke(query_obj.normalized_text)
            context = "\n".join(d.page_content for d in docs)

            # retriever의 prompt|llm 체인으로 답 생성
            answer = retriever.chain.invoke({
                "context": context,
                "question": query_obj.normalized_text
            })

            retriever_results.append({
                "retriever": name,
                "answer": answer,
                "context": context
            })

        # 6️⃣ Aggregator (기계적 병합) - Summarizer 입력용으로만 사용
        answers_for_merge = [(r["retriever"], r["answer"]) for r in retriever_results]
        aggregated_text = aggregator.aggregate(answers_for_merge)

        # 7️⃣ Summarizer (LLM 기반 최종 정리)
        final_answer = summarizer.summarize(aggregated_text)

        # 🔥 시간
        response_time = datetime.now(timezone.utc)
        latency_ms = round((time.perf_counter() - start_perf) * 1000, 2)

        # 🔥 Mongo 저장 (retriever별 context 포함 / aggregated_text는 저장 안 함)
        doc = {
            "query_id": query_obj.id,
            "raw_query": query_obj.raw_text,
            "normalized_query": query_obj.normalized_text,
            "grade": query_obj.grade,
            "retrievers_used": query_obj.retrievers,

            # 핵심
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