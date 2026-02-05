from abc import ABC, abstractmethod

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.output_parsers import StrOutputParser


class BaseRetriever(ABC):

    def __init__(self, folder_name):

        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large"
        )

        self.vectorstore = FAISS.load_local(
            folder_path=f"resources/vectorstore/{folder_name}",
            embeddings=self.embeddings,
            index_name="faiss_index",
            allow_dangerous_deserialization=True
        )

        self.retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": 3}
        )

        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0
        )

        self.prompt = self._build_prompt()

        self.chain = self.prompt | self.llm | StrOutputParser()

    @abstractmethod
    def _build_prompt(self):
        pass

    def invoke(self, question):

        docs = self.retriever.invoke(question)

        context = "\n".join([d.page_content for d in docs])

        return self.chain.invoke({
            "context": context,
            "question": question
        })