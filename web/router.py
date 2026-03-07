# main.py (async pipeline 적용 + Mongo 저장 + retriever별 context 저장 + 시간 측정 포함)

import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.services.input_service import InputService
from app.services.normalization_service import NormalizationService
from app.services.routing_service import RoutingService
from app.services.retriever_loader import RetrieverLoader
from app.services.aggregator_service import AggregatorService
from app.services.summarizer_service import SummarizerService
from app.services.logging_service import LoggingService

from app.core.llm_service import LLMService
from app.core.embedding_service import EmbeddingService

from infra.mongodb.mongo_client import MongoClientProvider
from infra.mongodb.query_log_repository import QueryLogRepository

from app.pipeline.pipeline import RagPipeline


load_dotenv()

app = FastAPI()

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

# 🔹 Pipeline
pipeline = RagPipeline(
    input_service=input_service,
    normalization_service=normalization_service,
    routing_service=routing_service,
    retriever_loader=retriever_loader,
    aggregator_service=aggregator,
    summarizer_service=summarizer,
    logging_service=logging_service,
)


class QueryInput(BaseModel):
    query: str


@app.post("/query")
async def query_endpoint(query_input: QueryInput):
    try:
        return await pipeline.run(query_input.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))