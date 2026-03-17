from langchain_ollama import ChatOllama


class LLMService:

    def __init__(self):
        self.llm = ChatOllama(
            model="exaone3.5:latest",
            temperature=0,
            num_ctx=32768
        )

    def get_llm(self):
        return self.llm