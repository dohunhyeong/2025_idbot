# RAG 시스템 3종 비교 평가 계획

## Context
법정감염병 챗봇의 RAG 시스템이 3단계로 발전했다. 전처리 여부, RAG 방식(Naive vs Advanced)에 따른 성능 차이를 LLM-as-Judge로 정량 평가하여 개선 효과를 검증한다.

## 평가 대상 3개 시스템

| 구분 | FAISS DB | RAG 방식 | LLM | Embedding |
|------|----------|----------|-----|-----------|
| **S1**: 전처리 X + Naive | `2024_proj_openai/data/faiss_index` | Simple chain (k=2) | gpt-3.5-turbo | text-embedding-3-large |
| **S2**: 전처리 O + Naive | `db/faiss_total/index` | Same chain (k=2) | gpt-3.5-turbo | text-embedding-3-large |
| **S3**: 전처리 O + Advanced | `2025_proj(hdh)/resources/vectorstore/` (12개) | Intent→Route→Retrieve→Summarize | exaone3.5:7.8b (Ollama) | bge-m3 (Ollama) |

## 평가 방식

### 참조 답변 부재
- `RAG_qa.xlsx`의 `answer` 컬럼은 **S1의 모델 답변**이며, 정답(ground truth)이 아님
- 따라서 참조 답변 기반 평가(accuracy)는 사용하지 않음

### 1. 절대 평가 (참조 답변 불필요)
질문-답변만으로 3가지 메트릭 평가:
- **relevance** (관련성): 답변이 질문에 직접 대답하는가 (1~5)
- **completeness** (완전성): 필요한 정보를 충분히 포함하는가 (1~5)
- **helpfulness** (유용성): 사용자에게 실질적으로 도움이 되는가 (1~5)
- **total_score** = 3개 평균

### 2. Pairwise 비교 (높은 신뢰도)
정답 없이도 두 답변을 직접 비교하여 승자를 판정:
- S1 vs S2 (전처리 효과)
- S2 vs S3 (Advanced RAG 효과)
- S1 vs S3 (전체 개선 효과)
- 결과: A 승리 / B 승리 / 동점

> Chatbot Arena 등에서 사용하는 방식으로, 참조 답변 없이도 신뢰도 높은 비교 가능

## 설정
- **평가 규모**: 697개 중 **무작위 100개** 샘플 (random_state=42 고정)
- **LLM Judge**: GPT-4o (temperature=0, json_object format)
- **API 호출**: 절대 평가 300회 + Pairwise 300회 = 총 600회 (~$2)
- **결과물 형태**: **Jupyter 노트북** 1개에 수집-평가-시각화 통합

---

## 구현 단계

### Step 1: System 1/2 FAISS 경로 환경변수화

**파일**: `2024_proj_openai/app/main.py` (line 52, 61)

```python
folder_path = os.getenv("FAISS_FOLDER_PATH", "./data")
index_name = os.getenv("FAISS_INDEX_NAME", "faiss_index")
```

S1은 기본값으로, S2는 환경변수 지정으로 실행.

### Step 2: 평가 노트북

**파일**: `evaluation/rag_comparison.ipynb`

| 셀 | 내용 |
|----|------|
| Cell 1 | 설정 & 임포트, RAG_qa.xlsx에서 100개 샘플 추출 (S1 답변 포함) |
| Cell 2 | async 답변 수집 함수 (run_batch_trace.py 패턴 재사용) |
| Cell 3 | S2 답변 수집 (port 8002) |
| Cell 4 | S3 답변 수집 (port 8000) |
| Cell 5 | 답변 병합 & `all_answers.xlsx` 저장 |
| Cell 6 | LLM-as-Judge 함수: `judge_absolute()` + `judge_pairwise()` |
| Cell 7 | 절대 평가 실행 (300회) → `eval_absolute.xlsx` |
| Cell 8 | Pairwise 비교 실행 (300회) → `eval_pairwise.xlsx` |
| Cell 9 | 요약 통계 (절대 평가 평균/표준편차 + Pairwise 승률) |
| Cell 10 | 시각화 1: Grouped bar chart (3 metrics × 3 systems) |
| Cell 11 | 시각화 2: Pairwise 승률 Stacked bar chart |
| Cell 12 | 시각화 3: total_score 분포 히스토그램 |
| Cell 13 | 시각화 4: 응답 시간 박스플롯 (S2, S3만) |
| Cell 14 | S1 vs S3 Pairwise에서 S3 승리/패배 질문 Top 5 |

---

## 실행 방법

```bash
# 터미널 1: S2 서버 (전처리된 FAISS DB)
cd ~/Documents/2024_proj_openai && \
FAISS_FOLDER_PATH=/Users/hyeongdohun/Documents/db/faiss_total \
FAISS_INDEX_NAME=index \
uvicorn app.main:app --port 8002

# 터미널 2: S3 서버 (Advanced RAG)
cd ~/Documents/2025_proj\(hdh\) && poetry run uvicorn main:app --port 8000
```

S1은 RAG_qa.xlsx에서 로드하므로 서버 실행 불필요.

---

## 핵심 수정/생성 파일

| 파일 | 변경 |
|------|------|
| `2024_proj_openai/app/main.py:52,61` | FAISS 경로 환경변수화 (2줄) |
| `evaluation/rag_comparison.ipynb` | **신규** - 평가 노트북 |
| `evaluation/results/` | **신규 디렉토리** - 결과 저장 |

## 재사용 코드

| 원본 | 재사용 내용 |
|------|------------|
| `run_batch_trace.py` (line 25-68) | async HTTP + semaphore 패턴 |
| `evaluate.ipynb` (cell 2) | judge 프롬프트 구조 (버그 수정: `.format()` → `string.Template`) |
| `evaluate.ipynb` (cell 5) | matplotlib 시각화 패턴 |

## 검증 방법

1. S2/S3 서버를 실행하고 노트북 셀을 순서대로 실행
2. `all_answers.xlsx`에서 3개 시스템 답변이 모두 채워졌는지 확인
3. `eval_absolute.xlsx`, `eval_pairwise.xlsx`에서 None이 없는지 확인
4. 시각화 차트에서 3개 시스템 비교 결과 확인
