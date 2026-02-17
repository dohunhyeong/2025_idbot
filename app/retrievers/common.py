from app.retrievers.base_retriever import BaseRetriever
from langchain_core.prompts import PromptTemplate


class CommonRetriever(BaseRetriever):

    def __init__(self, llm, embeddings):
        super().__init__("common", llm, embeddings)

    def _build_prompt(self):

        template = """
        당신은 감염병 일반 전문가입니다.

        반드시 제공된 Context 문서만 사용하여 답변하세요.
        문서에 없는 내용은 추측하지 마세요.

        Context:
        {context}

        Question:
        {question}

        Answer (한국어):
        """
        return PromptTemplate(
            input_variables=["context", "question"],
            template=template
        )