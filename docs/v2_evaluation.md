# 📋 [명세서] 법정감염병 RAG 시스템 3종 비교 평가 및 신뢰성 검증

## 1. 평가 목적
법정감염병 챗봇 RAG 시스템의 3단계 발전 과정(S1 → S2 → S3)에 따른 성능 향상을 정량적으로 검증함. 특히 **기술적 신뢰성(RAGAS)**과 **사용자 경험(Pairwise Win-rate)** 두 가지 측면에서 할루시네이션 감소와 답변 품질 개선을 입증하는 것이 핵심임.

## 2. 평가 대상 시스템

| 시스템 ID | 구분 | 주요 특징 | 실행 환경 |
|:---|:---|:---|:---|
| **S1** | **Naive (Baseline)** | 전처리 없는 원문 데이터 + 기초 RAG | `RAG_qa.xlsx` 내 기존 답변 활용 |
| **S2** | **Naive (Cleaned)** | 전처리 완료된 FAISS DB + 기초 RAG | `Port 8002` (Uvicorn 서버) |
| **S3** | **Advanced** | 전처리 + Multi-retriever + Intent Routing | `Port 8000` (Exaone 3.5 / Ollama) |

## 3. 데이터 파이프라인 및 샘플링

### 3.1 샘플링 전략
- **샘플 크기:** 전체 697개 질문 중 무작위 **100개** 추출.
- **재현성:** `random_state=42`로 고정.
- **필수 수집 항목:** 질문(Q), 시스템별 답변(A), **참조된 컨텍스트(C - 리스트 형태)**.

### 3.2 비동기 데이터 수집
- `asyncio`와 `Semaphore(limit=5)`를 사용하여 S2, S3 서버에 동시 요청.
- **필수 사항:** RAGAS 평가를 위해 S2와 S3 응답 시 반드시 **참조한 문서 리스트(List of strings)**가 포함되어야 함.

## 4. 이원화 평가 지표 (Dual-Layered Metrics)

### [Layer A] RAGAS: 기술적 신뢰성 (정답 데이터 미사용)
정답(Ground Truth) 없이 시스템의 내적 논리성과 환각 방지 능력을 측정함.
1.  **Faithfulness (충실도):** 답변의 모든 문장이 검색된 컨텍스트에 근거하는가? (**의학적 신뢰성 핵심 지표**)
2.  **Answer Relevancy (질문 관련성):** 답변이 사용자의 질문 의도에 직접적으로 부합하는가?

### [Layer B] LLM-as-a-Judge: 정성적 품질 평가
강력한 모델(GPT-4o)을 판사로 활용하여 실제 서비스 품질을 비교함.
1.  **Pairwise Comparison (SXS 비교):**
    - 비교군: [S1 vs S2], [S2 vs S3], [S1 vs S3]
    - 판정 기준: 의학적 정확성, 정보의 완전성, 가독성.
2.  **Absolute Scoring (절대 평가 1~5점):**
    - 지표: Relevance(관련성), Completeness(완전성), Helpfulness(유용성).

## 5. 분석 및 시각화 요구사항

### 5.1 통계 분석
- S2 대비 S3의 **Faithfulness 향상률(%)** 계산.
- 수치화된 **할루시네이션 감소율** 도출.
- 시스템별 평균 **응답 시간(Latency)** 비교 (S2 vs S3).

### 5.2 시각화 (Matplotlib/Seaborn)
- **Radar Chart:** S1, S2, S3의 절대 평가 3대 지표 평균 비교.
- **Stacked Bar Chart:** Pairwise 승률(Win/Loss/Tie) 분포.
- **Histogram:** 시스템별 `total_score` 분포도.
- **오답 분석 (Top 5):** S3의 Faithfulness 점수가 가장 낮은 케이스 5개를 추출하여 원인 분석용 데이터 생성.

## 6. 최종 리포트 목표 문구
"본 평가는 **Advanced RAG (S3)**가 사용자 선호도(Win-rate)를 **X% 향상**시킬 뿐만 아니라, RAGAS Faithfulness 지표 기준 할루시네이션 위험을 **Y% 감소**시켜 법정감염병 정보의 **의학적 신뢰성**을 확보했음을 증명해야 함."

---
### 개발자 참고 사항 (Developer Note)
- RAGAS 라이브러리 호환성을 위해 `contexts` 데이터는 반드시 `List[List[str]]` 구조를 유지할 것.
- f-string 사용 시 JSON 구조와 충돌을 방지하기 위해 프롬프트 엔지니어링에는 `string.Template` 사용 권장.