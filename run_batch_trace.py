"""
RAG_qa.xlsx의 question 컬럼 질문들을 /query 엔드포인트로 일괄 전송하고
Langfuse에 트레이싱하는 배치 스크립트.

사전 조건:
  - uvicorn으로 FastAPI 서버가 실행 중이어야 함 (`poetry run uvicorn main:app`)
  - .env에 LANGFUSE_* 환경변수가 설정되어 있어야 함

실행:
  poetry run python run_batch_trace.py
  poetry run python run_batch_trace.py --url http://localhost:8000 --concurrency 5 --input RAG_qa.xlsx
"""

import asyncio
import argparse
import json
import time
from pathlib import Path
from datetime import datetime

import httpx
import pandas as pd


async def send_query(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    idx: int,
    question: str,
    base_url: str,
    timeout: float,
) -> dict:
    """단일 질문을 /query로 전송하고 결과를 반환."""
    async with semaphore:
        start = time.perf_counter()
        try:
            response = await client.post(
                f"{base_url}/query",
                json={"query": question},
                timeout=timeout,
            )
            response.raise_for_status()
            data = response.json()
            latency = round((time.perf_counter() - start) * 1000, 2)
            print(f"[{idx+1:>4}] OK  | latency={latency:>8.1f}ms | {question[:40]!r}")
            return {
                "idx": idx,
                "question": question,
                "query_id": data.get("query_id"),
                "answer": data.get("answer"),
                "mode": data.get("mode") or _infer_mode(data),
                "latency_ms": data.get("latency_ms", latency),
                "status": "ok",
                "error": None,
            }
        except Exception as e:
            latency = round((time.perf_counter() - start) * 1000, 2)
            print(f"[{idx+1:>4}] ERR | latency={latency:>8.1f}ms | {question[:40]!r} -> {e}")
            return {
                "idx": idx,
                "question": question,
                "query_id": None,
                "answer": None,
                "mode": None,
                "latency_ms": latency,
                "status": "error",
                "error": str(e),
            }


def _infer_mode(data: dict) -> str | None:
    retrievers = data.get("retrievers_used")
    if retrievers is not None:
        return "rag" if retrievers else "intent_only"
    return None


async def run_batch(
    input_path: str,
    base_url: str,
    concurrency: int,
    timeout: float,
    output_path: str | None,
) -> None:
    df = pd.read_excel(input_path)
    if "question" not in df.columns:
        raise ValueError(f"'question' 컬럼을 찾을 수 없습니다. 실제 컬럼: {df.columns.tolist()}")

    questions = df["question"].tolist()
    total = len(questions)
    print(f"총 {total}개 질문 | 동시 요청 수={concurrency} (Ollama exaone3.5:7.8b) | 서버={base_url}")
    print("-" * 60)

    semaphore = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient() as client:
        tasks = [
            send_query(client, semaphore, idx, q, base_url, timeout)
            for idx, q in enumerate(questions)
        ]
        results = await asyncio.gather(*tasks)

    # 결과 정렬 (원본 순서 유지)
    results.sort(key=lambda r: r["idx"])

    ok_count = sum(1 for r in results if r["status"] == "ok")
    err_count = total - ok_count
    print("-" * 60)
    print(f"완료: {ok_count}/{total} 성공, {err_count} 실패")

    # 결과를 DataFrame으로 변환 후 저장
    result_df = pd.DataFrame(results).drop(columns=["idx"])

    if output_path is None:
        stem = Path(input_path).stem
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(Path(input_path).parent / f"{stem}_traced_{ts}.xlsx")

    result_df.to_excel(output_path, index=False)
    print(f"결과 저장: {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RAG 배치 트레이싱 스크립트")
    parser.add_argument("--input", default="RAG_qa.xlsx", help="입력 엑셀 파일 경로")
    parser.add_argument("--url", default="http://localhost:8000", help="FastAPI 서버 URL")
    parser.add_argument("--concurrency", type=int, default=2, help="동시 요청 수 (기본: 2, Ollama 로컬 모델 권장)")
    parser.add_argument("--timeout", type=float, default=120.0, help="요청 타임아웃(초, 기본: 120, Ollama 로컬 모델은 느릴 수 있음)")
    parser.add_argument("--output", default=None, help="출력 엑셀 경로 (기본: 자동 생성)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(
        run_batch(
            input_path=args.input,
            base_url=args.url,
            concurrency=args.concurrency,
            timeout=args.timeout,
            output_path=args.output,
        )
    )
