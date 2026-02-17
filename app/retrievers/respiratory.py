from app.retrievers.base_retriever import BaseRetriever
from langchain_core.prompts import PromptTemplate


class RespiratoryRetriever(BaseRetriever):

    def __init__(self, llm, embeddings):
        super().__init__("respiratory", llm, embeddings)

    def _build_prompt(self):

        template = """
        당신은 호흡기 감염병 전문가입니다.

        반드시 아래 Context 문서에 포함된 정보만 사용하여 답변하세요.
        문서에 없는 내용은 추측하거나 생성하지 마세요.

        특히 다음 내용을 중심으로 설명하세요:
        - 병원체 및 주요 증상
        - 전파 방식 (비말, 공기, 접촉 등)
        - 격리 기준 및 신고 체계
        - 예방 방법 (마스크, 백신 등)

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