import os


class QueryLogRepository:

    def __init__(self, db):
        collection_name = os.getenv("MONGODB_COLLECTION", "2026cidc")
        self.collection = db.get_collection(collection_name)

    async def insert_one(self, doc):
        result = await self.collection.insert_one(doc)
        return str(result.inserted_id)