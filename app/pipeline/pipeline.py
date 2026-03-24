import os
import time
import asyncio
from datetime import datetime, timezone

TRACE_NAME = os.getenv("TRACE_NAME", "RAG_RAGAS")


class RagPipeline:

    def __init__(
        self,
        *,
        input_service,
        intent_service,
        normalization_service,
        routing_service,
        retriever_loader,
        aggregator_service,
        summarizer_service,
        logging_service,
        grade_service,
        source_service,
        tracing_service,
    ):
        self.input_service = input_service
        self.intent_service = intent_service
        self.normalization_service = normalization_service
        self.routing_service = routing_service
        self.retriever_loader = retriever_loader
        self.aggregator_service = aggregator_service
        self.summarizer_service = summarizer_service
        self.logging_service = logging_service
        self.grade_service = grade_service
        self.source_service = source_service
        self.tracing_service = tracing_service

    async def run(self, user_query: str) -> dict:

        ts = self.tracing_service
        start_perf = time.perf_counter()
        query_time = datetime.now(timezone.utc)

        # 1️⃣ Query 생성
        query_obj = self.input_service.create_query(user_query)

        # [TRACE 시작]
        trace = ts.start_trace(trace_id=query_obj.id, name=TRACE_NAME, input=user_query)

        # 2️⃣ Intent 처리
        # [SPAN] intent_detection
        intent_span = ts.start_span(trace, name="intent_detection", input=query_obj.raw_text)
        intent = self.intent_service.detect_intent(query_obj.raw_text)
        ts.end_span(intent_span, output=intent)

        if intent in ["greeting", "meta", "disease_stats"]:

            final_answer = self.intent_service.build_response(
                intent,
                query_obj.raw_text
            )

            response_time = datetime.now(timezone.utc)
            latency_ms = round((time.perf_counter() - start_perf) * 1000, 2)

            ts.end_trace(trace, output=final_answer, metadata={"mode": "intent_only", "intent": intent, "latency_ms": latency_ms})
            ts.flush()

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
                "intent": intent
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

        # 3️⃣ 질병명 정규화
        # [SPAN] normalization
        norm_span = ts.start_span(trace, name="normalization", input=query_obj.raw_text)
        query_obj = self.normalization_service.normalize_query(query_obj)
        ts.end_span(norm_span, output=query_obj.normalized_text)

        # 4️⃣ 급수 질문 처리
        if self.grade_service.is_grade_question(query_obj.raw_text):

            final_answer = self.grade_service.build_answer(query_obj)

            response_time = datetime.now(timezone.utc)
            latency_ms = round((time.perf_counter() - start_perf) * 1000, 2)

            ts.end_trace(trace, output=final_answer, metadata={"mode": "grade_only", "grade": query_obj.grade, "latency_ms": latency_ms})
            ts.flush()

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

        # 5️⃣ 라우팅
        # [SPAN] routing
        routing_span = ts.start_span(trace, name="routing", input=query_obj.normalized_text)
        query_obj = self.routing_service.route_retrievers(query_obj)
        ts.end_span(routing_span, output=query_obj.retrievers)

        # 6️⃣ Retriever 로드
        retrievers = self.retriever_loader.load(query_obj.retrievers)

        # 7️⃣ 병렬 실행
        tasks = [
            r.ainvoke_with_context(query_obj.normalized_text)
            for r in retrievers
        ]

        results = await asyncio.gather(*tasks)

        retriever_results = []
        answers_for_merge = []
        common_urls = []
        all_contexts: list[str] = []

        for name, payload in zip(query_obj.retrievers, results):

            # [SPAN] retriever_{name}
            ret_span = ts.start_span(trace, name=f"retriever_{name}", input=query_obj.normalized_text)
            docs = payload.get("docs", [])
            ts.log_event(ret_span, name="retrieved_docs", body={
                "chunks": [
                    {"chunk_index": i, "content": doc.page_content, "metadata": doc.metadata}
                    for i, doc in enumerate(docs)
                ]
            })
            ts.log_event(ret_span, name="context_used", body={"context": payload["context"]})
            ts.end_span(ret_span, output=payload["answer"], metadata={"retriever_name": name, "doc_count": len(docs)})

            retriever_results.append({
                "retriever": name,
                "answer": payload["answer"],
                "context": payload["context"]
            })

            for doc in docs:
                chunk = doc.page_content.strip()
                if chunk and chunk not in all_contexts:
                    all_contexts.append(chunk)

            answers_for_merge.append((name, payload["answer"]))

            if name == "common":
                for doc in docs:
                    url = doc.metadata.get("source_url")
                    if url and url not in common_urls:
                        common_urls.append(url)

        # 8️⃣ Aggregation
        # [SPAN] aggregation
        agg_span = ts.start_span(trace, name="aggregation", input=answers_for_merge)
        aggregated_text = self.aggregator_service.aggregate(
            answers_for_merge
        )
        ts.end_span(agg_span, output=aggregated_text)

        # 9️⃣ Summarize
        # [SPAN] summarization
        sum_span = ts.start_span(trace, name="summarization", input=aggregated_text)
        final_answer = await self.summarizer_service.asummarize(
            aggregated_text
        )
        ts.end_span(sum_span, output=final_answer)

        # 🔟 출처 추가
        final_answer = self.source_service.append_sources(
            final_answer,
            common_urls
        )

        # 시간
        response_time = datetime.now(timezone.utc)
        latency_ms = round((time.perf_counter() - start_perf) * 1000, 2)

        # [TRACE 종료]
        ts.end_trace(trace, output=final_answer, metadata={
            "mode": "rag",
            "grade": query_obj.grade,
            "retrievers_used": query_obj.retrievers,
            "latency_ms": latency_ms,
        })
        ts.flush()

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
            "mode": "rag"
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
            "aggregated_text": aggregated_text,
            "contexts": all_contexts,
        }