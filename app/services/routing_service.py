import re


class RoutingService:

    def __init__(self):

        self.routing_rules = {

            "bioterror": ["탄저", "두창", "에볼라", "페스트"],

            "respiratory": [
                "인플루엔자", "코로나", "메르스", "사스",
                "호흡기", "폐렴", "결핵"
            ],

            "water_food": [
                "식중독", "살모넬라", "콜레라", "장염",
                "비브리오", "노로바이러스"
            ],

            "zoonotic": [
                "광견병", "브루셀라", "탄저", "야토병",
                "동물"
            ],

            "sexual_blood": [
                "에이즈", "HIV", "매독", "B형간염", "C형간염",
                "성병", "혈액"
            ],

            "vaccine": [
                "백신", "예방접종"
            ],

            "tick": [
                "쯔쯔가무시", "라임병", "SFTS",
                "진드기"
            ],

            "healthcare": [
                "MRSA", "CRE", "의료관련 감염",
                "병원감염"
            ],

            "etc": [
                "기생충", "말라리아", "열대병"
            ],

              "tb": [
                "결핵, tb"
            ]
        }

    def route_retrievers(self, query_obj):

        text = query_obj.normalized_text

        # ⭐ common 항상 포함
        query_obj.add_retriever("common")

        for retriever_name, keywords in self.routing_rules.items():

            for keyword in keywords:

                pattern = rf"\b{re.escape(keyword)}\b"

                if re.search(pattern, text):
                    query_obj.add_retriever(retriever_name)
                    break

        return query_obj