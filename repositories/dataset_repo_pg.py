from datetime import datetime
from typing import Any, Dict, List, Optional

import sqlalchemy as sa
from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import ChunkORM, DocumentORM, EmbeddingORM, TreeORM


class DatasetRepoPg:
    """Repository for dataset/knowledge base operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_datasets(self) -> List[Dict[str, Any]]:
        """List all datasets with their metadata"""
        # Since there's no dedicated dataset table, we'll aggregate from documents
        stmt = (
            select(
                DocumentORM.dataset_id,
                func.count(DocumentORM.doc_id).label("document_count"),
                func.min(DocumentORM.created_at).label("created_at"),
                func.max(DocumentORM.created_at).label("last_updated"),
            )
            .group_by(DocumentORM.dataset_id)
            .order_by(DocumentORM.dataset_id)
        )

        result = await self.session.execute(stmt)
        datasets = []

        for row in result:
            datasets.append(
                {
                    "id": row.dataset_id,
                    "name": row.dataset_id,  # Using dataset_id as name for now
                    "description": f"Knowledge base containing {row.document_count} documents",
                    "document_count": row.document_count,
                    "created_at": row.created_at,
                    "last_updated": row.last_updated,
                }
            )

        return datasets

    async def get_dataset_info(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific dataset"""
        # Get document count and timestamps
        doc_stmt = select(
            func.count(DocumentORM.doc_id).label("document_count"),
            func.min(DocumentORM.created_at).label("created_at"),
            func.max(DocumentORM.created_at).label("last_updated"),
        ).where(DocumentORM.dataset_id == dataset_id)

        doc_result = await self.session.execute(doc_stmt)
        doc_info = doc_result.first()

        if not doc_info or doc_info.document_count == 0:
            return None

        # Get chunk count
        chunk_stmt = (
            select(func.count(ChunkORM.id))
            .join(DocumentORM, ChunkORM.doc_id == DocumentORM.doc_id)
            .where(DocumentORM.dataset_id == dataset_id)
        )
        chunk_count = await self.session.scalar(chunk_stmt) or 0

        # Get embedding count
        emb_stmt = select(func.count(EmbeddingORM.id)).where(EmbeddingORM.dataset_id == dataset_id)
        embedding_count = await self.session.scalar(emb_stmt) or 0

        # Get tree count
        tree_stmt = select(func.count(TreeORM.tree_id)).where(TreeORM.dataset_id == dataset_id)
        tree_count = await self.session.scalar(tree_stmt) or 0

        return {
            "id": dataset_id,
            "name": dataset_id,
            "description": f"Knowledge base containing {doc_info.document_count} documents",
            "document_count": doc_info.document_count,
            "chunk_count": chunk_count,
            "embedding_count": embedding_count,
            "tree_count": tree_count,
            "created_at": doc_info.created_at,
            "last_updated": doc_info.last_updated,
            "status": "active",  # Could be derived from processing status
        }

    async def dataset_exists(self, dataset_id: str) -> bool:
        """Check if a dataset exists"""
        stmt = select(func.count(DocumentORM.doc_id)).where(DocumentORM.dataset_id == dataset_id)
        count = await self.session.scalar(stmt) or 0
        return count > 0

    async def get_dataset_documents(
        self, dataset_id: str, limit: Optional[int] = None, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get documents in a dataset with pagination"""
        stmt = (
            select(DocumentORM)
            .where(DocumentORM.dataset_id == dataset_id)
            .order_by(DocumentORM.created_at.desc())
            .offset(offset)
        )

        if limit:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        documents = []

        for doc in result.scalars():
            documents.append(
                {
                    "doc_id": doc.doc_id,
                    "source": doc.source,
                    "tags": doc.tags,
                    "extra_meta": doc.extra_meta,
                    "checksum": doc.checksum,
                    "created_at": doc.created_at,
                }
            )

        return documents

    async def delete_dataset(self, dataset_id: str) -> Dict[str, int]:
        """Delete all data associated with a dataset"""
        # This will cascade delete due to foreign key constraints
        # Delete documents (which will cascade to chunks)
        doc_stmt = sa.delete(DocumentORM).where(DocumentORM.dataset_id == dataset_id)
        doc_result = await self.session.execute(doc_stmt)

        # Delete embeddings
        emb_stmt = sa.delete(EmbeddingORM).where(EmbeddingORM.dataset_id == dataset_id)
        emb_result = await self.session.execute(emb_stmt)

        # Delete trees
        tree_stmt = sa.delete(TreeORM).where(TreeORM.dataset_id == dataset_id)
        tree_result = await self.session.execute(tree_stmt)

        return {
            "documents_deleted": doc_result.rowcount,
            "embeddings_deleted": emb_result.rowcount,
            "trees_deleted": tree_result.rowcount,
        }

    async def get_dataset_stats(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Get statistical information about a dataset"""
        if not await self.dataset_exists(dataset_id):
            return None

        # Get total token count from chunks
        token_stmt = (
            select(func.sum(ChunkORM.token_cnt))
            .join(DocumentORM, ChunkORM.doc_id == DocumentORM.doc_id)
            .where(DocumentORM.dataset_id == dataset_id)
        )
        total_tokens = await self.session.scalar(token_stmt) or 0

        # Get unique embedding models used
        model_stmt = select(distinct(EmbeddingORM.model)).where(
            EmbeddingORM.dataset_id == dataset_id
        )
        models_result = await self.session.execute(model_stmt)
        embedding_models = [row[0] for row in models_result]

        # Get processing status by looking at trees vs documents
        info = await self.get_dataset_info(dataset_id)
        if not info:
            return None

        processing_status = "completed" if info["tree_count"] > 0 else "pending"

        return {
            "dataset_id": dataset_id,
            "total_tokens": total_tokens,
            "embedding_models": embedding_models,
            "processing_status": processing_status,
            "has_embeddings": info["embedding_count"] > 0,
            "has_trees": info["tree_count"] > 0,
        }
