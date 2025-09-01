class EmbeddingService:
    def __init__(self, voyage_client_async):
        self.vo = voyage_client_async

    async def embed_query(self, text: str, *, byok_voyage_key: str | None, dim: int):
        if byok_voyage_key:
            self.vo.api_key = byok_voyage_key
        vecs = await self.vo.embed_queries([text])
        return vecs[0]
