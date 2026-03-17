FROM python:3.11-slim

# 시스템 의존성
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치
RUN pip install --no-cache-dir poetry==2.1.1

WORKDIR /app

# 의존성만 먼저 복사 (레이어 캐시 활용)
COPY pyproject.toml poetry.lock ./

# 가상환경 없이 시스템에 직접 설치
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

# 소스 코드 복사
COPY main.py ./
COPY app/ ./app/
COPY infra/ ./infra/
COPY resources/ ./resources/
COPY web/ ./web/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
