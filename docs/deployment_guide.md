# 배포 가이드

> 환경: Mac (Apple Silicon) → Ubuntu 22.04 서버 (RTX 4090), Docker
> 최종 업데이트: 2026-03-10

---

## 아키텍처

```
[ 사용자 브라우저 ]
        │
        │ HTTP :80
        ▼
┌──────────────────────────────────────────────┐
│  Docker: busan-chatbot                       │
│  (dohun123/busan-chatbot-frontend:latest)    │
│                                              │
│  ┌──────────────────────────────────────┐    │
│  │  Nginx :80                           │    │
│  │                                      │    │
│  │  /query, /admin/logs                 │    │
│  │    → proxy_pass http://backend:8000  │    │
│  │                                      │    │
│  │  /  → SPA (index.html)               │    │
│  └──────────────────────────────────────┘    │
└──────────────────────┬───────────────────────┘
                       │
                       │ Docker Network: busan-net
                       │ (alias: backend)
                       ▼
┌──────────────────────────────────────────────┐
│  Docker: busancidc-back2                     │
│  (dohun123/busancidc-back:latest)            │
│                                              │
│  FastAPI + Uvicorn :8000                     │
│                                              │
│  POST /query                                 │
│    → RAG Pipeline                            │
│      → FAISS 검색                            │
│      → Ollama (LLM / Embeddings)             │
│      → MongoDB 로그 저장                     │
└──────────┬───────────────────────┬───────────┘
           │                       │
           │ host.docker.internal  │ Docker Network: busan-net
           │ :11434                │
           ▼                       ▼
┌──────────────────┐   ┌───────────────────────┐
│  Ollama          │   │  Docker: mongodb      │
│  (Host 설치)     │   │  mongo :37017         │
│                  │   │                       │
│  exaone3.5:7.8b  │   │  DB: openai           │
│  bge-m3          │   │  Collection: 2026cidc │
│  GPU: RTX 4090   │   │                       │
└──────────────────┘   └───────────────────────┘
```

### 컨테이너 및 네트워크 구성

| 컨테이너 | 이미지 | 포트 | 네트워크 | 별칭 |
|---------|-------|------|---------|------|
| busan-chatbot | dohun123/busan-chatbot-frontend:latest | 80:80 | busan-net | busan-chatbot |
| busancidc-back2 | dohun123/busancidc-back:latest | 8000:8000 | busan-net | backend |
| mongodb | mongo | 37017:27017 | busan-net | mongodb |
| Ollama | Host (비컨테이너) | 11434 | — | host.docker.internal |

---

## 사전 준비

### 서버 요구사항
- Ubuntu 22.04
- Docker 설치
- NVIDIA GPU + 드라이버 (RTX 4090)
- Ollama 설치 및 모델 pull 완료

```bash
# Ollama 모델 확인
ollama list
# exaone3.5:7.8b, bge-m3 이 있어야 함
```

### 로컬(Mac) 요구사항
- Docker Desktop (buildx 포함)
- Docker Hub 계정 로그인

---

## Step 1. 이미지 빌드 및 푸시 (로컬 Mac)

Mac(Apple Silicon)은 기본적으로 `arm64`로 빌드되므로, 서버(amd64)용으로 명시적으로 빌드해야 합니다.

```bash
# buildx 빌더 생성 (최초 1회)
docker buildx create --use

# linux/amd64 이미지 빌드 및 Docker Hub 푸시
docker buildx build \
  --platform linux/amd64 \
  -t dohun123/busancidc-back:latest \
  --push \
  .
```

> **주의:** `FROM --platform=linux/amd64`를 Dockerfile에 하드코딩하는 것보다
> 빌드 시 `--platform` 옵션으로 지정하는 것을 권장합니다.

---

## Step 2. 서버 환경 설정

### .env 파일 생성

서버 홈 디렉토리에 아래 내용으로 `.env` 파일을 생성합니다.

```env
MONGODB_URI=mongodb://openai:pw_509@211.54.28.173:37017/openai?authSource=openai
MONGODB_DB=openai
MONGODB_COLLECTION=2026cidc
ADMIN_TOKEN=busancidc2026
PORT=8000
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

### Ollama 서비스 시작

```bash
sudo systemctl start ollama

# 재부팅 후 자동 시작 설정 (권장)
sudo systemctl enable ollama
```

---

## Step 3. Docker 네트워크 확인

프론트엔드(`busan-chatbot`)가 속한 네트워크를 확인합니다.

```bash
docker inspect busan-chatbot --format '{{json .NetworkSettings.Networks}}' | python3 -m json.tool
```

`busan-net`에 속해 있는지 확인합니다. 이후 백엔드 컨테이너도 동일한 네트워크에 연결해야 합니다.

---

## Step 4. 백엔드 컨테이너 실행

> **`--network-alias backend`가 필요한 이유**
>
> 프론트엔드 이미지에 포함된 `nginx.conf`는 백엔드 요청을 `http://backend:8000`으로 전달하도록 고정되어 있습니다.
> 따라서 Docker 네트워크 안에서 백엔드 컨테이너가 반드시 `backend`라는 이름으로 식별되어야 합니다.
> `--network-alias backend` 옵션이 그 역할을 합니다. 이 옵션이 없으면 Nginx가 `backend` 호스트를 찾지 못해 502 에러가 발생합니다.

```bash
docker run -d \
  --name busancidc-back2 \
  -p 8000:8000 \
  --env-file .env \
  --add-host=host.docker.internal:host-gateway \
  --network busan-net \
  --network-alias backend \
  dohun123/busancidc-back:latest
```

| 옵션 | 설명 |
|------|------|
| `--env-file .env` | 환경변수 파일 주입 |
| `--add-host=host.docker.internal:host-gateway` | 컨테이너에서 호스트(Ollama)에 접근하기 위한 설정 |
| `--network busan-net` | 프론트엔드와 같은 네트워크 |
| `--network-alias backend` | Nginx의 `proxy_pass http://backend:8000` 과 매칭 |

---

## Step 5. Nginx 재로드

컨테이너 실행 후 Nginx가 `backend` 호스트명을 인식하도록 reload합니다.

```bash
docker exec busan-chatbot nginx -s reload
```

> 네트워크 구성 변경 후에는 항상 실행해야 합니다.

---

## Step 6. 동작 확인

### 백엔드 직접 테스트

```bash
curl http://localhost:8000/query \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"query":"에볼라"}'
```

### Nginx 통해 전체 테스트

```bash
curl http://localhost/query \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"query":"에볼라"}' | python3 -m json.tool | grep latency_ms
```

### GPU 사용 확인

```bash
nvidia-smi
ollama ps
# PROCESSOR 항목이 "100% GPU" 이어야 함
```

---

## Nginx 설정 (참고)

`busan-chatbot` 컨테이너 내부 `/etc/nginx/conf.d/default.conf`:

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    proxy_read_timeout 600;
    proxy_connect_timeout 600;
    proxy_send_timeout 600;

    location /query {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /admin/logs {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

> `proxy_*_timeout 600`은 LLM 응답 시간이 길기 때문에 필수입니다.
> 기본값(60초)이면 504 Gateway Timeout이 발생합니다.

---

## NVIDIA 드라이버 버전 고정

Ubuntu 자동 업데이트가 NVIDIA 드라이버를 올려버리면, 재부팅 전까지 커널 모듈과 버전 불일치가 발생해 GPU를 사용하지 못합니다.
초기 배포 시 아래 명령어로 드라이버 버전을 고정해두는 것을 권장합니다.

```bash
sudo apt-mark hold \
  nvidia-driver-570 \
  libnvidia-compute-570 \
  libnvidia-extra-570 \
  libnvidia-gl-570 \
  nvidia-dkms-570 \
  nvidia-kernel-source-570
```

확인:
```bash
sudo apt-mark showhold
```

> 나중에 드라이버를 업데이트하고 싶다면 hold를 해제한 뒤 수동으로 진행하고 즉시 재부팅합니다:
> ```bash
> sudo apt-mark unhold nvidia-driver-570
> sudo apt upgrade nvidia-driver-570
> sudo reboot
> ```

---

## 재배포 시 절차

```bash
# 1. 로컬에서 새 이미지 빌드 및 푸시
docker buildx build --platform linux/amd64 -t dohun123/busancidc-back:latest --push .

# 2. 서버에서 기존 컨테이너 교체
docker rm -f busancidc-back2
docker pull dohun123/busancidc-back:latest
docker run -d \
  --name busancidc-back2 \
  -p 8000:8000 \
  --env-file .env \
  --add-host=host.docker.internal:host-gateway \
  --network busan-net \
  --network-alias backend \
  dohun123/busancidc-back:latest

# 3. Nginx 재로드
docker exec busan-chatbot nginx -s reload
```
