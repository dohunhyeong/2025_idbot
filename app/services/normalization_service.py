import pandas as pd
import re
from pathlib import Path


class NormalizationService:

    NA_SET = {"na", "n/a", "none", "null", ""}

    def __init__(self):
        metadata_path = Path("resources/metadata/disease_metadata.csv")
        self.df = pd.read_csv(metadata_path).fillna("")

    def normalize_query(self, query_obj):

        text = query_obj.raw_text

        for _, row in self.df.iterrows():

            kor_name = str(row.get("kor_name", "")).strip()
            grade = row.get("grade", "")

            if not kor_name:
                continue

            synonyms = [
                row.get("kor_name", ""),
                row.get("eng_name", ""),
                row.get("Abbreviation", ""),
                row.get("synonym_1", ""),
                row.get("synonym_2", ""),
                row.get("synonym_3", ""),
                row.get("synonym_4", ""),
            ]

            for synonym in synonyms:

                synonym = str(synonym).strip()

                if not synonym or synonym.lower() in self.NA_SET:
                    continue

                # 🔥 핵심: 한글도 정규식 사용
                pattern = rf"{re.escape(synonym)}"

                if re.search(pattern, text, flags=re.IGNORECASE):

                    text = re.sub(pattern, kor_name, text, flags=re.IGNORECASE)

                    query_obj.update_normalized(text)

                    try:
                        query_obj.set_grade(int(float(grade)))
                    except:
                        pass

                    return query_obj

        return query_obj