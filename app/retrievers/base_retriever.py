from abc import ABC, abstractmethod
import asyncio
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser

class BaseRetriever(ABC):
    def __init__(self, folder_name, llm, embeddings):
        self.vectorstore = FAISS.load_local(
            folder_path=f"resources/vectorstore/{folder_name}",
            embeddings=embeddings,
            index_name="index",  # 네 파일명(index.faiss/index.pkl)에 맞춘 값
            allow_dangerous_deserialization=True
        )

        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
        self.llm = llm
        self.prompt = self._build_prompt()
        self.chain = self.prompt | self.llm | StrOutputParser()

    @abstractmethod
    def _build_prompt(self):
        pass

    # (옵션) 동기 버전 유지
    def invoke(self, question: str) -> str:
        docs = self.retriever.invoke(question)
        context = "\n".join(d.page_content for d in docs)
        return self.chain.invoke({"context": context, "question": question})

    # ✅ 비동기: retriever 검색 + 체인 호출을 thread로 실행
    async def ainvoke_with_context(self, question: str) -> dict:
        docs = await asyncio.to_thread(self.retriever.invoke, question)
        context = "\n".join(d.page_content for d in docs)

        answer = await asyncio.to_thread(
            self.chain.invoke,
            {"context": context, "question": question}
        )

        return {"answer": answer, "context": context}