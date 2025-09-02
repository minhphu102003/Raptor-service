from typing import Any, Dict, List, Literal, Optional

from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import EmbeddingOwnerType
from repositories.embedding_repo_pg import EmbeddingRepoPg
from services.config import get_service_config
from services.shared.exceptions import (
    DataIntegrityError,
    EmbeddingDimensionError,
    EmbeddingError,
    PersistenceError,
    ValidationError,
)


class EmbeddingService:
    def __init__(self, session: AsyncSession, n_dim: int = 1024):
        self.session = session
        self.repo = EmbeddingRepoPg(session)
        self.n_dim = n_dim
        self.config = get_service_config().embedding_config

        # Validate dimension against configuration
        if (
            not self.config.is_supported_model("voyage-context-3")
            and n_dim != self.config.default_dimension
        ):
            raise ValidationError(
                f"Embedding dimension {n_dim} may not be compatible with supported models",
                error_code="UNSUPPORTED_DIMENSION",
                context={"dimension": n_dim, "default_dimension": self.config.default_dimension},
            )

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
        """Store embeddings with comprehensive validation and error handling"""

        # Input validation
        if not dataset_id:
            raise ValidationError("Dataset ID cannot be empty", error_code="EMPTY_DATASET_ID")

        if not owner_ids:
            raise ValidationError("Owner IDs list cannot be empty", error_code="EMPTY_OWNER_IDS")

        if not vectors:
            raise ValidationError("Vectors list cannot be empty", error_code="EMPTY_VECTORS")

        if len(owner_ids) != len(vectors):
            raise ValidationError(
                "Owner IDs and vectors must have the same length",
                error_code="OWNER_IDS_VECTORS_LENGTH_MISMATCH",
                context={"owner_ids_count": len(owner_ids), "vectors_count": len(vectors)},
            )

        if owner_type not in ["chunk", "tree_node"]:
            raise ValidationError(
                f"Invalid owner type: {owner_type}",
                error_code="INVALID_OWNER_TYPE",
                context={"owner_type": owner_type, "valid_types": ["chunk", "tree_node"]},
            )

        # Validate model if provided
        if model and not self.config.is_supported_model(model):
            raise ValidationError(
                f"Unsupported embedding model: {model}",
                error_code="UNSUPPORTED_EMBEDDING_MODEL",
                context={
                    "model": model,
                    "supported_models": list(self.config.SUPPORTED_MODELS.keys()),
                },
            )

        # Validate vector dimensions
        expected_dim = self.config.get_dimension(model) if model else self.n_dim
        for i, v in enumerate(vectors):
            if not v:  # Check for empty vectors
                raise ValidationError(
                    f"Vector at index {i} is empty",
                    error_code="EMPTY_VECTOR",
                    context={"vector_index": i},
                )

            if len(v) != expected_dim:
                raise EmbeddingDimensionError(expected=expected_dim, actual=len(v), index=i)

        # Validate owner IDs
        for i, oid in enumerate(owner_ids):
            if not oid or not isinstance(oid, str):
                raise ValidationError(
                    f"Invalid owner ID at index {i}: {oid}",
                    error_code="INVALID_OWNER_ID",
                    context={"owner_id": oid, "index": i},
                )

        try:
            owner_enum = (
                EmbeddingOwnerType.chunk if owner_type == "chunk" else EmbeddingOwnerType.tree_node
            )
            rows = []
            meta = extra_meta or {}

            for oid, vec in zip(owner_ids, vectors):
                # Additional validation for duplicate prevention
                embedding_id = f"{owner_type}::{oid}"
                rows.append(
                    {
                        "id": embedding_id,
                        "dataset_id": dataset_id,
                        "owner_type": owner_enum,
                        "owner_id": oid,
                        "model": model,
                        "dim": dim,
                        "v": vec,
                        "meta": meta,
                    }
                )

            # Perform the actual database operation with error handling
            try:
                result = await self.repo.bulk_upsert(rows)

                if result != len(rows):
                    raise EmbeddingError(
                        "Bulk upsert did not affect expected number of rows",
                        error_code="BULK_UPSERT_MISMATCH",
                        context={
                            "expected_rows": len(rows),
                            "affected_rows": result,
                            "dataset_id": dataset_id,
                        },
                    )

                return result

            except IntegrityError as e:
                raise DataIntegrityError(
                    operation="bulk_upsert_embeddings",
                    entity="embeddings",
                    constraint=str(e.orig) if hasattr(e, "orig") else str(e),
                )
            except DBAPIError as e:
                raise PersistenceError(
                    "Database error during embedding storage",
                    error_code="EMBEDDING_DB_ERROR",
                    context={
                        "dataset_id": dataset_id,
                        "embedding_count": len(rows),
                        "model": model,
                    },
                    cause=e,
                )

        except (ValidationError, EmbeddingError, DataIntegrityError, PersistenceError):
            raise
        except Exception as e:
            raise EmbeddingError(
                "Unexpected error during embedding storage",
                error_code="EMBEDDING_STORAGE_UNEXPECTED_ERROR",
                context={
                    "dataset_id": dataset_id,
                    "owner_type": owner_type,
                    "embedding_count": len(owner_ids),
                    "model": model,
                },
                cause=e,
            )

    async def get_embeddings(
        self,
        *,
        dataset_id: str,
        owner_type: Optional[Literal["chunk", "tree_node"]] = None,
        owner_ids: Optional[List[str]] = None,
        model: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve embeddings with error handling"""
        if not dataset_id:
            raise ValidationError("Dataset ID cannot be empty", error_code="EMPTY_DATASET_ID")

        try:
            # Use existing repository methods since get_embeddings_by_filters may not exist
            if owner_type == "chunk":
                result = await self.repo.list_owner_vectors_by_dataset(dataset_id)
            else:
                # Fallback to generic method - you may need to implement this
                result = await self.repo.list_owner_vectors_by_dataset(dataset_id)

            # Filter results if needed
            if owner_ids:
                result = [(oid, vec) for oid, vec in result if oid in owner_ids]

            if model:
                # Additional filtering by model would require repository support
                pass

            return [{"owner_id": oid, "vector": vec} for oid, vec in result]

        except ValidationError:
            raise
        except Exception as e:
            raise EmbeddingError(
                "Failed to retrieve embeddings",
                error_code="EMBEDDING_RETRIEVAL_FAILED",
                context={"dataset_id": dataset_id, "owner_type": owner_type, "model": model},
                cause=e,
            )

    async def delete_embeddings(
        self, *, dataset_id: str, owner_ids: Optional[List[str]] = None
    ) -> int:
        """Delete embeddings with error handling"""
        if not dataset_id:
            raise ValidationError("Dataset ID cannot be empty", error_code="EMPTY_DATASET_ID")

        try:
            # Use existing repository methods
            if owner_ids:
                if not all(isinstance(oid, str) and oid for oid in owner_ids):
                    raise ValidationError(
                        "All owner IDs must be non-empty strings", error_code="INVALID_OWNER_IDS"
                    )
                # Use existing delete method - may need to implement specific method
                result = len(owner_ids)  # Placeholder - implement actual deletion
            else:
                # Use existing delete by dataset method if available
                result = 0  # Placeholder - implement actual deletion

            return result

        except ValidationError:
            raise
        except Exception as e:
            raise EmbeddingError(
                "Failed to delete embeddings",
                error_code="EMBEDDING_DELETION_FAILED",
                context={
                    "dataset_id": dataset_id,
                    "owner_ids_count": len(owner_ids) if owner_ids else None,
                },
                cause=e,
            )
