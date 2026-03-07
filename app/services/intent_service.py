import re


class IntentService:

    def __init__(self):
        # greeting 의도
        self.greeting_regex = re.compile(
            r"(안녕|안녕하세요|하이|반가워|헬로|hello)",
            re.IGNORECASE
        )

        # 챗봇 정체/기능 관련 meta 질문
        self.meta_regex = re.compile(
            r"(너\s?누구|누구야|누가\s?만들|개발자|"
            r"이름\s?뭐|정체|뭐\s?할\s?수|"
            r"무슨\s?기능|어떤\s?기능|"
            r"무엇을\s?할\s?수|뭐하는\s?봇|"
            r"누가\s?개발|누가\s?만들었)",
            re.IGNORECASE
        )

    def detect_intent(self, text: str) -> str:
        normalized = (text or "").strip()

        # greeting
        if self.greeting_regex.search(normalized):
            return "greeting"

        # meta
        if self.meta_regex.search(normalized):
            return "meta"

        # 나머지는 질병 질문
        return "disease"

    def build_response(self, intent: str) -> str:

        if intent == "greeting":
            return (
                "안녕하세요. 저는 법정 감염병 정보를 안내하는 AI 챗봇입니다."
            )

        if intent == "meta":
            return (
                "저는 법정 감염병 정보를 안내하는 AI 챗봇입니다. "
                "부산감염병관리지원단의 요청으로 국립부경대학교 디지털스마트부산 아카데미의 "
                "주진범, 형도훈에 의해 개발되었습니다. "
                "감염병의 정의, 증상, 전파 경로, 예방 방법, 신고 기준 등의 정보를 안내할 수 있습니다."
            )

        return ""