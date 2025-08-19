from typing import Any, Dict, List, Literal, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from infra.db.models import EmbeddingOwnerType
from interfaces_adaptor.repositories.embedding_repo_pg import EmbeddingRepoPg


class EmbeddingService:
    def __init__(self, session: AsyncSession, n_dim: int = 1024):
        self.session = session
        self.repo = EmbeddingRepoPg(session)
        self.n_dim = n_dim

    async def store_embeddings(
        self,
        *,
        dataset_id: str,
        owner_type: Literal["chunk", "tree_node"],
        owner_ids: List[str],
        vectors: List[List[float]],
        model: str = "voyage-3",
        dim: int = 1024,
        extra_meta: Optional[Dict[str, Any]] = None,
    ) -> int:
        if len(owner_ids) != len(vectors):
            raise ValueError("owner_ids và vectors phải cùng độ dài")
        for i, v in enumerate(vectors):
            if len(v) != self.n_dim:
                raise ValueError(f"vector[{i}] có dim={len(v)} != {self.n_dim}")

        owner_enum = (
            EmbeddingOwnerType.chunk if owner_type == "chunk" else EmbeddingOwnerType.tree_node
        )
        rows = []
        meta = extra_meta or {}
        for oid, vec in zip(owner_ids, vectors):
            rows.append(
                {
                    "id": f"{owner_type}::{oid}",
                    "dataset_id": dataset_id,
                    "owner_type": owner_enum,
                    "owner_id": oid,
                    "model": model,
                    "dim": dim,
                    "v": vec,
                    "meta": meta,
                }
            )
        return await self.repo.bulk_upsert(rows)
