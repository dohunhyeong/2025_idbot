import pandas as pd
import re
from pathlib import Path


class NormalizationService:

    def __init__(self):

        metadata_path = Path("resources/metadata/disease_metadata.csv")
        self.df = pd.read_csv(metadata_path).fillna("")

    def normalize_query(self, query_obj):

        text = query_obj.raw_text

        for _, row in self.df.iterrows():

            name = row["name"]
            grade = row["Grade"]

            synonyms = [
                row.get("name", ""),
                row.get("synonym_1", ""),
                row.get("synonym_2", ""),
                row.get("synonym_3", ""),
                row.get("synonym_4", ""),
            ]

            for synonym in synonyms:

                if not synonym:
                    continue

                # 단어 경계 매칭
                pattern = rf"\b{re.escape(synonym)}\b"

                if re.search(pattern, text):

                    new_text = re.sub(pattern, name, text)

                    query_obj.update_normalized(new_text)
                    query_obj.set_grade(int(grade))

                    return