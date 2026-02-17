from app.retrievers.base_retriever import BaseRetriever
from langchain_core.prompts import PromptTemplate


class WaterFoodRetriever(BaseRetriever):

    def __init__(self, llm, embeddings):
        super().__init__("water_food", llm, embeddings)

    def _build_prompt(self):

        template = """
        당신은 수인성 및 식품매개 감염병 전문가입니다.

        반드시 아래 Context 문서의 정보만 사용하여 답변하세요.
        문서에 없는 내용은 절대 추측하거나 생성하지 마세요.

        특히 다음 사항을 중심으로 설명하세요:

        - 오염 경로 (물, 음식, 해산물 등)
        - 주요 증상 및 잠복기
        - 집단발생 가능성
        - 예방 방법 (위생관리, 식품 조리 등)
        - 신고 및 관리 체계

        Context:
        {context}

        Question:
        {question}

        Answer (한국어, 전문적이고 구조적으로 작성):
        """

        return PromptTemplate(
            input_variables=["context", "question"],
            template=template
        )