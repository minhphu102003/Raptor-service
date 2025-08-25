from infra.embeddings.openai_embeddings import call_openai_embeddings
from interfaces_adaptor.ports import IEmbedder


class OpenAIEmbedder(IEmbedder):
    def __init__(
        self,
        model: str,
        api_key: str,
        space="cosine",
        normalized=True,
        target_dim: int | None = None,
    ):
        self.model = model
        self._api_key = api_key
        self.space = space
        self.normalized = normalized
        self.dim = target_dim or (3072 if "3-large" in model else 1536)

    async def embed(self, texts, *, batch_size=64):
        return await call_openai_embeddings(
            api_key=self._api_key,
            model=self.model,
            texts=texts,
            batch_size=batch_size,
            dimensions=self.dim,
        )
