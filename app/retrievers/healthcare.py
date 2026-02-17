from app.retrievers.base_retriever import BaseRetriever
from langchain_core.prompts import PromptTemplate


class HealthcareRetriever(BaseRetriever):

    def __init__(self, llm, embeddings):
        super().__init__("healthcare", llm, embeddings)

    def _build_prompt(self):

        template = """
        당신은 의료관련 감염(Healthcare-Associated Infection, HAI) 전문가입니다.

        아래 제공된 Context 문서의 내용만 사용하여 답변하세요.
        문서에 없는 내용은 절대 추측하거나 생성하지 마세요.

        특히 다음 사항을 중점적으로 설명하세요:
        - 병원 내 전파 경로
        - 내성균 여부 (예: MRSA, CRE 등)
        - 감염 관리 및 격리 조치
        - 예방 및 대응 전략

        Context:
        {context}

        Question:
        {question}

        Answer (한국어, 임상적으로 정확하게):
        """

        return PromptTemplate(
            input_variables=["context", "question"],
            template=template
        )