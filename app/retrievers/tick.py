from app.retrievers.base_retriever import BaseRetriever
from langchain_core.prompts import PromptTemplate


class TickRetriever(BaseRetriever):

    def __init__(self, llm, embeddings):
        super().__init__("tick", llm, embeddings)

    def _build_prompt(self):

        template = """
        당신은 진드기 매개 감염병 전문가입니다.

        반드시 아래 Context 문서에 포함된 정보만 사용하여 답변하세요.
        문서에 없는 내용은 절대 추측하거나 생성하지 마세요.

        특히 다음 내용을 중심으로 설명하세요:

        - 병원체 및 전파 경로 (진드기 매개 여부)
        - 주요 증상 및 합병증
        - 고위험군
        - 예방법 (야외활동 시 주의사항 등)
        - 신고 및 관리 체계

        Context:
        {context}

        Question:
        {question}

        Answer (한국어, 전문적이고 체계적으로 작성):
        """

        return PromptTemplate(
            input_variables=["context", "question"],
            template=template
        )