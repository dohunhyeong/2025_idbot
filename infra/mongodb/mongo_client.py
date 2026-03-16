import os
from motor.motor_asyncio import AsyncIOMotorClient


class MongoClientProvider:
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            uri = os.getenv("MONGODB_URI")
            cls._client = AsyncIOMotorClient(uri)
        return cls._client