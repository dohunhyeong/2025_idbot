from app.retrievers.base_retriever import BaseRetriever
from langchain_core.prompts import PromptTemplate


class BioterrorRetriever(BaseRetriever):

    def __init__(self, llm, embeddings):
        super().__init__("bioterror", llm, embeddings)

    def _build_prompt(self):

        template = """
        당신은 생물테러 및 고위험 감염병 전문가입니다.

        아래 Context 문서에 포함된 정보만을 사용하여 답변하세요.
        문서에 없는 내용은 절대 추측하거나 생성하지 마세요.

        특히 다음 사항을 중점적으로 설명하세요:
        - 병원체 특성
        - 전파 방식
        - 위험도 및 대응 수준
        - 격리 및 신고 체계

        Context:
        {context}

        Question:
        {question}

        Answer (한국어, 전문적이고 정확하게):
        """

        return PromptTemplate(
            input_variables=["context", "question"],
            template=template
        )