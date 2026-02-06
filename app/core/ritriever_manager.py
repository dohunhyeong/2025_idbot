from app.core.llm_service import LLMService
from app.core.embedding_service import EmbeddingService
from app.retrievers.common import CommonRetriever
from app.retrievers.respiratory import RespiratoryRetriever
# ... 나머지 import


class RetrieverManager:

    def __init__(self):

        self.llm = LLMService().get_llm()
        self.embeddings = EmbeddingService().get_embeddings()

        self.registry = {
            "common": CommonRetriever(self.llm, self.embeddings),
            "respiratory": RespiratoryRetriever(self.llm, self.embeddings),
            # ... 나머지
        }

    def invoke(self, query_obj):

        results = []

        for name in query_obj.retrievers:
            retriever = self.registry.get(name)
            if retriever:
                results.append(
                    retriever.invoke(query_obj.normalized_text)
                )

        return results