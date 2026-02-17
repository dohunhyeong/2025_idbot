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

            name = str(row.get("name", "")).strip()
            grade = row.get("Grade", "")

            # name이 없으면 스킵
            if not name:
                continue

            synonyms = [
                row.get("name", ""),
                row.get("synonym_1", ""),
                row.get("synonym_2", ""),
                row.get("synonym_3", ""),
                row.get("synonym_4", ""),
            ]

            for synonym in synonyms:

                synonym = str(synonym).strip()

                # 빈 값 / Na / NA 등 제거
                if not synonym or synonym.lower() in {"na", "n/a", "none"}:
                    continue

                # 단어 경계 매칭 (영문 약어 대응 위해 IGNORECASE)
                pattern = rf"\b{re.escape(synonym)}\b"

                if re.search(pattern, text, flags=re.IGNORECASE):

                    new_text = re.sub(pattern, name, text, flags=re.IGNORECASE)

                    query_obj.update_normalized(new_text)

                    # Grade가 비어있지 않을 때만 저장
                    try:
                        query_obj.set_grade(int(grade))
                    except Exception:
                        pass

                    return query_obj  # ✅ 반드시 query_obj 반환

        return query_obj  # ✅ 매칭이 없어도 query_obj 반환