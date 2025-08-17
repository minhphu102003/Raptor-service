class VoyageEmbeddingClientAsync:
    async def embed_cce_full_doc(
        self, doc: str, model="voyage-context-3", out_dim=1024, out_dtype="float", chunk_fn=None
    ):
        import voyageai

        fn = chunk_fn or voyageai.default_chunk_fn
        r = await self._client.contextualized_embed(
            inputs=[[doc]],
            model=model,
            input_type="document",
            output_dimension=out_dim,
            output_dtype=out_dtype,
            chunk_fn=fn,
        )
        return r.results[0].embeddings, r.results[0].chunk_texts
