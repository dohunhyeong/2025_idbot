import re


class IntentService:

    def __init__(self):

        # -----------------------------
        # 감염병 통계
        # -----------------------------
        self.disease_stats = {
            "1급": 18,
            "2급": 22,
            "3급": 32,
            "4급": 60
        }

        self.total_diseases = sum(self.disease_stats.values())

        # -----------------------------
        # Intent Regex
        # -----------------------------

        # 인사
        self.greeting_regex = re.compile(
            r"(안녕|안녕하세요|하이|반가워|hello|hi)",
            re.IGNORECASE
        )

        # 챗봇 소개 / 기능 질문
        self.meta_regex = re.compile(
            r"(너\s?누구|누구야|개발자|누가\s?만들|"
            r"이름\s?뭐|정체|뭐\s?할\s?수|"
            r"무슨\s?기능|어떤\s?기능|"
            r"뭐하는\s?봇|누가\s?개발)",
            re.IGNORECASE
        )

        # 감염병 개수 질문
        self.stats_regex = re.compile(
            r"(법정\s?감염병.*몇|감염병.*몇|[1-4]급\s?감염병.*몇)",
            re.IGNORECASE
        )

    # -------------------------------------------------
    # Intent Detection
    # -------------------------------------------------

    def detect_intent(self, text: str) -> str:

        text = (text or "").strip()

        if self.greeting_regex.search(text):
            return "greeting"

        if self.meta_regex.search(text):
            return "meta"

        if self.stats_regex.search(text):
            return "disease_stats"

        return "disease"

    # -------------------------------------------------
    # Intent Response
    # -------------------------------------------------

    def build_response(self, intent: str, text: str = "") -> str:

        text = (text or "").strip()

        # 인사
        if intent == "greeting":
            return "안녕하세요. 저는 법정 감염병 정보를 안내하는 AI 챗봇입니다."

        # 챗봇 소개
        if intent == "meta":
            return (
                "저는 법정 감염병 정보를 안내하는 AI 챗봇입니다. "
                "부산감염병관리지원단의 요청으로 국립부경대학교 디지털스마트부산 아카데미의 "
                "주진범, 형도훈에 의해 개발되었습니다. "
                "감염병의 정의, 증상, 전파 경로, 예방 방법, 신고 기준 등의 정보를 안내할 수 있습니다."
            )

        # 감염병 통계 질문
        if intent == "disease_stats":

            for grade, count in self.disease_stats.items():
                if grade in text:
                    return f"현재 {grade} 법정 감염병은 {count}종입니다."

            return (
                f"현재 법정 감염병은 총 {self.total_diseases}종이며 "
                f"1급 {self.disease_stats['1급']}종, "
                f"2급 {self.disease_stats['2급']}종, "
                f"3급 {self.disease_stats['3급']}종, "
                f"4급 {self.disease_stats['4급']}종으로 구성되어 있습니다."
            )

        return ""