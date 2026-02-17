class AggregatorService:

    def aggregate(self, answers: list[tuple[str, str]]) -> str:
        """
        answers: [(retriever_name, answer_text), ...]
        """

        blocks = []
        seen = set()

        for name, text in answers:
            if not text:
                continue

            cleaned = text.strip()
            if not cleaned:
                continue

            # 동일 답변 완전 중복 제거(약하게)
            if cleaned in seen:
                continue
            seen.add(cleaned)

            blocks.append(f"## {name}\n{cleaned}")

        return "\n\n".join(blocks)