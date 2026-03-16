from langchain_ollama import OllamaEmbeddings


class EmbeddingService:

    def __init__(self):
        self.embeddings = OllamaEmbeddings(
            model="bge-m3"
        )

    def get_embeddings(self):
        return self.embeddings