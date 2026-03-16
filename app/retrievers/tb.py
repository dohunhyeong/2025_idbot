from app.retrievers.base_retriever import BaseRetriever
from langchain_core.prompts import PromptTemplate


class TbRetriever(BaseRetriever):

    def __init__(self, llm, embeddings):
        super().__init__("tb", llm, embeddings)

    def _build_prompt(self):

        template = """
        당신은 결핵(Tuberculosis) 전문 감염병 전문가입니다.

        반드시 아래 Context 문서의 정보만 사용하여 답변하세요.
        문서에 없는 내용은 절대 추측하거나 생성하지 마세요.

        특히 다음 사항을 중심으로 설명하세요:

        - 결핵의 병원체 및 전파 방식
        - 잠복결핵과 활동성 결핵의 차이
        - 주요 증상
        - 치료 기간 및 약제
        - 신고 등급 및 관리 체계

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