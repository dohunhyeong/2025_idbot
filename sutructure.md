project/

 ├ app/                        # 핵심 비즈니스 로직 (Brain)
 │
 │   ├ models/                 # 도메인 객체
 │   │   ├ query.py
 │   │   ├ answer.py
 │   │   └ retriever_interface.py
 │
 │   ├ services/               # 단일 기능 서비스
 │   │   ├ input_service.py
 │   │   ├ routing_service.py
 │   │   └ logging_service.py
 │
 │   └ pipeline/               # RAG 실행 흐름
 │       └ rag_pipeline.py
 │
 ├ infra/                      # 외부 시스템 연결 (Hands)
 │
 │   ├ vector_db/
 │   │   └ vector_store.py
 │
 │   ├ mongodb/
 │   │   └ mongo_repository.py
 │
 │   └ llm_client/
 │       └ openai_client.py
 │
 ├ resources/                  # 지식 데이터 및 인덱스
 │
 │   ├ metadata/
 │   │   └ disease_metadata.csv
 │
 │   └ vectorstore/
 │       └ (FAISS / Chroma index 저장)
 │
 ├ web/                        # 사용자 인터페이스
 │
 │   ├ templates/
 │   ├ static/
 │   └ router.py
 │
 ├ tests/
 │
 ├ main.py
 └ pyproject.toml