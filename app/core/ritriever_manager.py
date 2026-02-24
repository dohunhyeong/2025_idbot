from app.retrievers.common import CommonRetriever
from app.retrievers.respiratory import RespiratoryRetriever
from app.retrievers.bioterror_A import BioterrorRetriever_A
from app.retrievers.bioterror_B import BioterrorRetriever_B
from app.retrievers.water_food import WaterFoodRetriever
from app.retrievers.zoonotic import ZoonoticRetriever
from app.retrievers.etc import EtcRetriever
from app.retrievers.tick import TickRetriever
from app.retrievers.sexual_blood import SexualBloodRetriever
from app.retrievers.vaccine import VaccineRetriever
from app.retrievers.tb import TbRetriever
from app.retrievers.healthcare import HealthcareRetriever
class RetrieverManager:

    def __init__(self, llm, embeddings):

        self.llm = llm
        self.embeddings = embeddings

        # 🔹 Retriever 인스턴스 registry
        self.registry = {
            "common": CommonRetriever(self.llm, self.embeddings),
            "bioterror_A": BioterrorRetriever_A(self.llm, self.embeddings),
            "bioterror_B": BioterrorRetriever_B(self.llm, self.embeddings),
            "respiratory": RespiratoryRetriever(self.llm, self.embeddings),
            "water_food": WaterFoodRetriever(self.llm, self.embeddings),
            "zoonotic": ZoonoticRetriever(self.llm, self.embeddings),
            "sexual_blood": SexualBloodRetriever(self.llm, self.embeddings),
            "vaccine": VaccineRetriever(self.llm, self.embeddings),
            "tick": TickRetriever(self.llm, self.embeddings),
            "healthcare": HealthcareRetriever(self.llm, self.embeddings),
            "etc": EtcRetriever(self.llm, self.embeddings),
            "tb": TbRetriever(self.llm, self.embeddings),
        }

    def invoke(self, query_obj):

        results = []

        for name in query_obj.retrievers:

            retriever = self.registry.get(name)

            if not retriever:
                continue

            result = retriever.invoke(query_obj.normalized_text)

            results.append({
                "retriever": name,
                "answer": result
            })

        return results