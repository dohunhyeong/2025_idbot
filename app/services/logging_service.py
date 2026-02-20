class LoggingService:

    def __init__(self, repo):
        self.repo = repo

    async def save(self, doc):
        return await self.repo.insert_one(doc)