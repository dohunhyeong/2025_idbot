import asyncio
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


class SummarizerService:
    def __init__(self, llm):
        self.llm = llm
        self.prompt = self._build_prompt()
        self.chain = self.prompt | self.llm | StrOutputParser()

    def _build_prompt(self):
        template = """
        다음은 여러 감염병 전문 리트리버가 생성한 답변입니다.

        중복을 제거하고,
        핵심 정보만 정리하여,
        하나의 자연스러운 최종 답변으로 작성하세요.

        만약 질병의 급수 또는 급을 물어 볼 경우 'grade'의 값을 급으로 인식해주세요.

        Content:
        {content}

        Final Answer (한국어):
        """
        return PromptTemplate(input_variables=["content"], template=template)

    def summarize(self, aggregated_text: str) -> str:
        return self.chain.invoke({"content": aggregated_text})

    # ✅ 비동기: LLM 호출을 thread로 오프로딩
    async def asummarize(self, aggregated_text: str) -> str:
        return await asyncio.to_thread(self.chain.invoke, {"content": aggregated_text})