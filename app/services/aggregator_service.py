class AggregatorService:

    def aggregate(self, answers: list[tuple[str, str]]) -> str:

        blocks = []
        seen = set()

        for name, text in answers:
            if not text:
                continue

            cleaned = text.strip()
            if not cleaned:
                continue

            if cleaned in seen:
                continue
            seen.add(cleaned)

            blocks.append(f"## {name}\n{cleaned}")

        return "\n\n".join(blocks)