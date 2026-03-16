from app.retrievers.base_retriever import BaseRetriever
from langchain_core.prompts import PromptTemplate


class SexualBloodRetriever(BaseRetriever):

    def __init__(self, llm, embeddings):
        super().__init__("sexual_blood", llm, embeddings)

    def _build_prompt(self):

        template = """
        당신은 성매개 및 혈액매개 감염병 전문가입니다.

        반드시 아래 제공된 Context 문서의 정보만 사용하여 답변하세요.
        문서에 없는 내용은 절대 추측하거나 생성하지 마세요.

        특히 다음 내용을 중심으로 설명하세요:
        - 주요 전파 경로 (성접촉, 혈액, 수직감염 등)
        - 주요 증상 및 합병증
        - 검사 방법 및 치료 가능 여부
        - 예방 전략 (콘돔 사용, 백신, 혈액관리 등)

        Context:
        {context}

        Question:
        {question}

        Answer (한국어, 의학적으로 정확하게 작성):
        """

        return PromptTemplate(
            input_variables=["context", "question"],
            template=template
        )