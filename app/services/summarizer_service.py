from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


class SummarizerService:

    def __init__(self, llm):
        self.llm = llm
        self.prompt = self._build_prompt()
        self.chain = self.prompt | self.llm | StrOutputParser()

    def _build_prompt(self):

        template = """
        다음은 여러 리트리버가 Context 문서만 기반으로 생성한 답변들입니다.

        규칙:
        - Content에 없는 사실을 추가/추측하지 마세요.
        - 중복 표현은 제거하되, 의미/사실을 바꾸지 마세요.
        - 최종 답변은 한국어로, 핵심 위주로 자연스럽게 작성하세요.
        - Content가 불충분하면 "제공된 문서만으로는 확답하기 어렵습니다."라고 말하세요.

        Content:
        {content}

        Final Answer (한국어):
        """

        return PromptTemplate(
            input_variables=["content"],
            template=template
        )

    def summarize(self, aggregated_text: str) -> str:
        return self.chain.invoke({"content": aggregated_text})