import os
from datetime import datetime
from typing import Any, Optional

from bson import ObjectId


class QueryLogRepository:
    def __init__(self, db):
        collection_name = os.getenv("MONGODB_COLLECTION", "2026cidc")
        self.collection = db.get_collection(collection_name)

    async def insert_one(self, doc: dict) -> str:
        result = await self.collection.insert_one(doc)
        return str(result.inserted_id)

    # ✅ 최신 로그 목록 조회 (페이징)
    async def find_recent(self, limit: int = 50, skip: int = 0) -> list[dict]:
        cursor = (
            self.collection.find({}, sort=[("query_time", -1)])
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [self._serialize(d) for d in docs]

    # ✅ id(ObjectId)로 단건 조회
    async def find_by_id(self, mongo_id: str) -> Optional[dict]:
        doc = await self.collection.find_one({"_id": ObjectId(mongo_id)})
        return self._serialize(doc) if doc else None

    # ✅ 텍스트 검색 (raw_query / normalized_query)
    async def search(self, q: str, limit: int = 50, skip: int = 0) -> list[dict]:
        query = {
            "$or": [
                {"raw_query": {"$regex": q, "$options": "i"}},
                {"normalized_query": {"$regex": q, "$options": "i"}},
            ]
        }
        cursor = (
            self.collection.find(query, sort=[("query_time", -1)])
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [self._serialize(d) for d in docs]

    def _serialize(self, doc: Optional[dict]) -> dict:
        if not doc:
            return {}
        doc["_id"] = str(doc["_id"])
        # datetime은 JSON 직렬화가 애매하니 ISO로 변환
        for k in ("query_time", "response_time"):
            if k in doc and isinstance(doc[k], datetime):
                doc[k] = doc[k].isoformat()
        return doc