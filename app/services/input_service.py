from app.models.query import Query


class InputService:

    def create_query(self, user_input: str) -> Query:

        if not user_input or not user_input.strip():
            raise ValueError("질문이 비어있습니다.")

        cleaned = user_input.strip()

        query = Query(cleaned)

        return query