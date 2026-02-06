class AggregatorService:

    def aggregate(self, answers: list[str]) -> str:

        # 🔹 None 제거
        cleaned = [a.strip() for a in answers if a]

        # 🔹 중복 제거 (순서 유지)
        unique = list(dict.fromkeys(cleaned))

        # 🔹 단순 병합
        combined = "\n\n".join(unique)

        return combined