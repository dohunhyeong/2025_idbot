from app.retrievers.base_retriever import BaseRetriever
from langchain_core.prompts import PromptTemplate


class EtcRetriever(BaseRetriever):

    def __init__(self, llm, embeddings):
        super().__init__("etc", llm, embeddings)

    def _build_prompt(self):

        template = """
        당신은 기타 감염병 분야 전문가입니다.

        아래 제공된 Context 문서에 포함된 정보만 사용하여 답변하세요.
        문서에 없는 내용은 절대 추측하거나 생성하지 마세요.

        특정 범주에 속하지 않는 감염병에 대해 다음 사항을 중심으로 설명하세요:

        - 병원체 및 주요 특징
        - 전파 방식
        - 주요 증상
        - 예방 및 관리 방법
        - 신고 및 관리 체계

        Context:
        {context}

        Question:
        {question}

        Answer (한국어, 명확하고 구조적으로 작성):
        """

        return PromptTemplate(
            input_variables=["context", "question"],
            template=template
        )