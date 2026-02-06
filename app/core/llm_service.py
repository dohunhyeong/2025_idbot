from langchain_ollama import ChatOllama


class LLMService:

    def __init__(self):
        self.llm = ChatOllama(
            model="exaone3.5:7.8b",
            temperature=0,
            num_ctx=32768
        )

    def get_llm(self):
        return self.llm