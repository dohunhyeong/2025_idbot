import re


class GradeService:
    # "몇 급" 류 질의 판별 패턴
    _PATTERNS = [
        r"몇\s*급",
        r"급\s*감염병",
        r"급수",
        r"등급",
        r"\bgrade\b",
        r"\bclass\b",
    ]

    def is_grade_question(self, text: str) -> bool:
        if not text:
            return False
        return any(re.search(p, text, flags=re.IGNORECASE) for p in self._PATTERNS)

    def build_answer(self, query_obj) -> str:
        # 정규화가 성공하면 grade가 세팅되어 있음
        if query_obj.grade is None:
            return "질병명이 확인되지 않아 급수를 알 수 없습니다. 예) '디프테리아는 몇 급 감염병인가요?'"

        # disease_name 필드를 따로 안 두는 현재 구조에서는 normalized_text를 그대로 씀
        return f"해당 감염병은 **{query_obj.grade}급**입니다."