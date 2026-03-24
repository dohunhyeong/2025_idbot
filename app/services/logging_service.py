class LoggingService:

    def __init__(self, repo):
        self.repo = repo

    async def save(self, doc):
        try:
            return await self.repo.insert_one(doc)
        except Exception:
            return None