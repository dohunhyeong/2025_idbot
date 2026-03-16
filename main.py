import os
import logging
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.pipeline.pipeline import RagPipeline

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
from app.core.tracing_service import TracingService

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

# Tracing
tracing_service = TracingService()

# LLM
llm = LLMService().get_llm()
embeddings = EmbeddingService().get_embeddings()

# Services
input_service = InputService()
intent_service = IntentService()
grade_service = GradeService()
normalization_service = NormalizationService()
routing_service = RoutingService()

retriever_loader = RetrieverLoader(llm, embeddings)
aggregator = AggregatorService()
summarizer = SummarizerService(llm)
source_service = SourceService()

# Mongo
mongo_client = MongoClientProvider.get_client()
mongo_db = mongo_client.get_database(os.getenv("MONGODB_DB", "openai"))
query_repo = QueryLogRepository(mongo_db)
logging_service = LoggingService(query_repo)

# Pipeline
pipeline = RagPipeline(
    input_service=input_service,
    intent_service=intent_service,
    normalization_service=normalization_service,
    routing_service=routing_service,
    retriever_loader=retriever_loader,
    aggregator_service=aggregator,
    summarizer_service=summarizer,
    logging_service=logging_service,
    grade_service=grade_service,
    source_service=source_service,
    tracing_service=tracing_service,
)


class QueryInput(BaseModel):
    query: str


@app.post("/query")
async def query_endpoint(query_input: QueryInput):

    try:
        result = await pipeline.run(query_input.query)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))