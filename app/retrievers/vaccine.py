from app.retrievers.base_retriever import BaseRetriever
from langchain_core.prompts import PromptTemplate


class VaccineRetriever(BaseRetriever):

    def __init__(self, llm, embeddings):
        super().__init__("vaccine", llm, embeddings)

    def _build_prompt(self):

        template = """
        당신은 감염병 백신 및 예방접종 전문가입니다.

        반드시 아래 Context 문서의 정보만 사용하여 답변하세요.
        문서에 없는 내용은 절대 추측하거나 생성하지 마세요.

        특히 다음 내용을 중심으로 설명하세요:

        - 해당 질병의 백신 존재 여부
        - 예방접종 대상 및 접종 일정
        - 추가 접종(부스터) 필요 여부
        - 금기사항 및 주의사항
        - 국가예방접종사업(NIP) 해당 여부

        Context:
        {context}

        Question:
        {question}

        Answer (한국어, 명확하고 체계적으로 작성):
        """

        return PromptTemplate(
            input_variables=["context", "question"],
            template=template
        )