import time
import asyncio
from datetime import datetime, timezone


class RagPipeline:
    def __init__(
        self,
        *,
        input_service,
        intent_service,              # ✅ 추가
        normalization_service,
        routing_service,
        retriever_loader,
        aggregator_service,
        summarizer_service,
        logging_service,
        grade_service,
    ):
        self.input_service = input_service
        self.intent_service = intent_service      # ✅ 추가
        self.normalization_service = normalization_service
        self.routing_service = routing_service
        self.retriever_loader = retriever_loader
        self.aggregator_service = aggregator_service
        self.summarizer_service = summarizer_service
        self.logging_service = logging_service
        self.grade_service = grade_service

    async def run(self, user_query: str) -> dict:

        start_perf = time.perf_counter()
        query_time = datetime.now(timezone.utc)

        # 1️⃣ Query 객체 생성
        query_obj = self.input_service.create_query(user_query)

        # -------------------------------------------------
        # ✅ 1.5 Intent 질문 처리 (인사 / 메타 질문)
        # -------------------------------------------------
        intent = self.intent_service.detect_intent(query_obj.raw_text)

        if intent in ["greeting", "meta"]:

            final_answer = self.intent_service.build_response(intent)

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
                "mode": "intent_only",
                "intent": intent,
            }

            mongo_id = await self.logging_service.save(doc)

            return {
                "query_id": query_obj.id,
                "mongo_id": mongo_id,
                "raw_query": query_obj.raw_text,
                "normalized_query": query_obj.raw_text,
                "grade": None,
                "retrievers_used": [],
                "latency_ms": latency_ms,
                "answer": final_answer,
            }

        # -------------------------------------------------
        # 2️⃣ 질병명 정규화
        # -------------------------------------------------
        query_obj = self.normalization_service.normalize_query(query_obj)

        # -------------------------------------------------
        # 2.5️⃣ 급수 질문 처리
        # -------------------------------------------------
        if self.grade_service.is_grade_question(query_obj.raw_text):

            final_answer = self.grade_service.build_answer(query_obj)

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
                "mode": "grade_only",
            }

            mongo_id = await self.logging_service.save(doc)

            return {
                "query_id": query_obj.id,
                "mongo_id": mongo_id,
                "raw_query": query_obj.raw_text,
                "normalized_query": query_obj.normalized_text,
                "grade": query_obj.grade,
                "retrievers_used": [],
                "latency_ms": latency_ms,
                "answer": final_answer,
            }

        # -------------------------------------------------
        # 3️⃣ 라우팅
        # -------------------------------------------------
        query_obj = self.routing_service.route_retrievers(query_obj)

        # -------------------------------------------------
        # 4️⃣ Retriever 로드
        # -------------------------------------------------
        retrievers = self.retriever_loader.load(query_obj.retrievers)

        # -------------------------------------------------
        # 5️⃣ Retriever 병렬 실행
        # -------------------------------------------------
        tasks = [
            r.ainvoke_with_context(query_obj.normalized_text)
            for r in retrievers
        ]

        results = await asyncio.gather(*tasks)

        retriever_results = []
        answers_for_merge = []

        for name, payload in zip(query_obj.retrievers, results):

            retriever_results.append({
                "retriever": name,
                "answer": payload["answer"],
                "context": payload["context"],
            })

            answers_for_merge.append((name, payload["answer"]))

        # -------------------------------------------------
        # 6️⃣ Aggregator
        # -------------------------------------------------
        aggregated_text = await self.aggregator_service.aggregate(answers_for_merge)

        # -------------------------------------------------
        # 7️⃣ Summarizer
        # -------------------------------------------------
        final_answer = await self.summarizer_service.asummarize(aggregated_text)

        # -------------------------------------------------
        # 8️⃣ 시간
        # -------------------------------------------------
        response_time = datetime.now(timezone.utc)

        latency_ms = round(
            (time.perf_counter() - start_perf) * 1000,
            2
        )

        # -------------------------------------------------
        # 9️⃣ Mongo 저장
        # -------------------------------------------------
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
            "latency_ms": latency_ms,
            "mode": "rag",
        }

        mongo_id = await self.logging_service.save(doc)

        return {
            "query_id": query_obj.id,
            "mongo_id": mongo_id,
            "raw_query": query_obj.raw_text,
            "normalized_query": query_obj.normalized_text,
            "grade": query_obj.grade,
            "retrievers_used": query_obj.retrievers,
            "latency_ms": latency_ms,
            "answer": final_answer,
        }