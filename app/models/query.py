from datetime import datetime, timezone
import uuid


class Query:

    def __init__(self, raw_text: str):

        self.id = str(uuid.uuid4())

        self.raw_text = raw_text
        self.normalized_text = raw_text

        # 질병 급수
        self.grade = None

        # 선택된 리트리버 목록
        self.retrievers = []

        self.created_at = datetime.now(timezone.utc)

    def update_normalized(self, new_text: str):
        self.normalized_text = new_text

    def set_grade(self, grade: int):
        self.grade = grade

    def add_retriever(self, retriever_name: str):

        if retriever_name not in self.retrievers:
            self.retrievers.append(retriever_name)