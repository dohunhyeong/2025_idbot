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


class QueryInput(BaseModel):
    query: str


@app.post("/query")
async def query_endpoint(query_input: QueryInput):

    try:
        # 1️⃣ Query 객체 생성
        query_obj = input_service.create_query(query_input.query)

        # 2️⃣ 동의어 정규화 + 급수 설정
        query_obj = normalization_service.normalize_query(query_obj)

        # 3️⃣ 라우팅 (사용할 retriever 결정)
        query_obj = routing_service.route_retrievers(query_obj)

        # 4️⃣ Retriever 객체 생성
        retrievers = retriever_loader.load(query_obj.retrievers)

        # 5️⃣ 각 retriever 실행
        answers = [
            r.invoke(query_obj.normalized_text)
            for r in retrievers
        ]

        # 6️⃣ Aggregator (기계적 병합)
        aggregated_text = aggregator.aggregate(answers)

        # 7️⃣ Summarizer (LLM 기반 최종 정리)
        final_answer = summarizer.summarize(aggregated_text)

        return {
            "query_id": query_obj.id,
            "raw_query": query_obj.raw_text,
            "normalized_query": query_obj.normalized_text,
            "grade": query_obj.grade,
            "retrievers_used": query_obj.retrievers,
            "answer": final_answer
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))