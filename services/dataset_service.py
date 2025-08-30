from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

from repositories.dataset_repo_pg import DatasetRepoPg
from services.exceptions import ServiceError, ValidationError

logger = logging.getLogger(__name__)


class DatasetService:
    """Service layer for dataset/knowledge base operations"""

    def __init__(self, container):
        self.container = container

    async def list_datasets(self) -> List[Dict[str, Any]]:
        """List all available datasets/knowledge bases"""
        try:
            async with self.container.make_uow() as uow:
                repo = DatasetRepoPg(uow.session)
                datasets = await repo.list_datasets()

                # Enhance datasets with additional computed fields
                for dataset in datasets:
                    dataset["title"] = dataset["name"]  # Add title field for UI
                    if dataset["document_count"] == 1:
                        dataset["description"] = f"Knowledge base with 1 document"
                    else:
                        dataset["description"] = (
                            f"Knowledge base with {dataset['document_count']} documents"
                        )

                return datasets
        except Exception as e:
            logger.error(f"Failed to list datasets: {e}")
            raise ServiceError(
                "Failed to retrieve datasets", error_code="DATASET_LIST_FAILED", cause=e
            )

    async def get_dataset_details(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific dataset"""
        if not dataset_id or not dataset_id.strip():
            raise ValidationError("Dataset ID cannot be empty")

        try:
            async with self.container.make_uow() as uow:
                repo = DatasetRepoPg(uow.session)
                dataset_info = await repo.get_dataset_info(dataset_id)

                if not dataset_info:
                    return None

                # Get additional statistics
                stats = await repo.get_dataset_stats(dataset_id)
                if stats:
                    dataset_info.update(stats)

                return dataset_info
        except Exception as e:
            logger.error(f"Failed to get dataset details for {dataset_id}: {e}")
            raise ServiceError(
                f"Failed to retrieve dataset details for {dataset_id}",
                error_code="DATASET_DETAILS_FAILED",
                cause=e,
            )

    async def dataset_exists(self, dataset_id: str) -> bool:
        """Check if a dataset exists"""
        if not dataset_id:
            return False

        try:
            async with self.container.make_uow() as uow:
                repo = DatasetRepoPg(uow.session)
                return await repo.dataset_exists(dataset_id)
        except Exception as e:
            logger.error(f"Failed to check dataset existence for {dataset_id}: {e}")
            return False

    async def get_dataset_documents(
        self, dataset_id: str, page: int = 1, page_size: int = 20
    ) -> Dict[str, Any]:
        """Get documents in a dataset with pagination"""
        if not dataset_id or not dataset_id.strip():
            raise ValidationError("Dataset ID cannot be empty")

        if page < 1:
            raise ValidationError("Page must be >= 1")

        if page_size < 1 or page_size > 100:
            raise ValidationError("Page size must be between 1 and 100")

        try:
            async with self.container.make_uow() as uow:
                repo = DatasetRepoPg(uow.session)

                # Check if dataset exists
                if not await repo.dataset_exists(dataset_id):
                    raise ValidationError(f"Dataset {dataset_id} not found")

                offset = (page - 1) * page_size
                documents = await repo.get_dataset_documents(
                    dataset_id=dataset_id, limit=page_size, offset=offset
                )

                # Get total count for pagination
                dataset_info = await repo.get_dataset_info(dataset_id)
                total_documents = dataset_info["document_count"] if dataset_info else 0

                return {
                    "documents": documents,
                    "pagination": {
                        "page": page,
                        "page_size": page_size,
                        "total": total_documents,
                        "pages": (total_documents + page_size - 1) // page_size,
                    },
                }
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to get documents for dataset {dataset_id}: {e}")
            raise ServiceError(
                f"Failed to retrieve documents for dataset {dataset_id}",
                error_code="DATASET_DOCUMENTS_FAILED",
                cause=e,
            )

    async def delete_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """Delete a dataset and all associated data"""
        if not dataset_id or not dataset_id.strip():
            raise ValidationError("Dataset ID cannot be empty")

        try:
            async with self.container.make_uow() as uow:
                repo = DatasetRepoPg(uow.session)

                # Check if dataset exists
                if not await repo.dataset_exists(dataset_id):
                    raise ValidationError(f"Dataset {dataset_id} not found")

                # Get info before deletion for the response
                dataset_info = await repo.get_dataset_info(dataset_id)

                # Delete the dataset
                deletion_stats = await repo.delete_dataset(dataset_id)

                logger.info(f"Deleted dataset {dataset_id}: {deletion_stats}")

                return {
                    "dataset_id": dataset_id,
                    "deleted_at": datetime.utcnow().isoformat(),
                    "deletion_stats": deletion_stats,
                    "original_info": dataset_info,
                }
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete dataset {dataset_id}: {e}")
            raise ServiceError(
                f"Failed to delete dataset {dataset_id}",
                error_code="DATASET_DELETE_FAILED",
                cause=e,
            )

    async def get_dataset_statistics(self, dataset_id: str) -> Dict[str, Any]:
        """Get comprehensive statistics for a dataset"""
        if not dataset_id or not dataset_id.strip():
            raise ValidationError("Dataset ID cannot be empty")

        try:
            async with self.container.make_uow() as uow:
                repo = DatasetRepoPg(uow.session)

                if not await repo.dataset_exists(dataset_id):
                    raise ValidationError(f"Dataset {dataset_id} not found")

                stats = await repo.get_dataset_stats(dataset_id)
                info = await repo.get_dataset_info(dataset_id)

                if not stats or not info:
                    raise ServiceError(f"Failed to retrieve statistics for dataset {dataset_id}")

                # Combine statistics and info
                result = {**info, **stats}

                # Add computed metrics
                if result["chunk_count"] > 0 and result["total_tokens"] > 0:
                    result["avg_tokens_per_chunk"] = result["total_tokens"] / result["chunk_count"]
                else:
                    result["avg_tokens_per_chunk"] = 0

                if result["document_count"] > 0:
                    result["avg_chunks_per_document"] = (
                        result["chunk_count"] / result["document_count"]
                    )
                else:
                    result["avg_chunks_per_document"] = 0

                return result
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to get statistics for dataset {dataset_id}: {e}")
            raise ServiceError(
                f"Failed to retrieve statistics for dataset {dataset_id}",
                error_code="DATASET_STATS_FAILED",
                cause=e,
            )

    async def validate_dataset_for_upload(self, dataset_id: str) -> Dict[str, Any]:
        """Validate if a dataset is ready for document upload"""
        if not dataset_id or not dataset_id.strip():
            raise ValidationError("Dataset ID cannot be empty")

        # Dataset ID validation rules
        if len(dataset_id) < 2:
            raise ValidationError("Dataset ID must be at least 2 characters long")

        if len(dataset_id) > 64:
            raise ValidationError("Dataset ID cannot exceed 64 characters")

        # Check for valid characters (alphanumeric, hyphens, underscores)
        import re

        if not re.match(r"^[a-zA-Z0-9_-]+$", dataset_id):
            raise ValidationError(
                "Dataset ID can only contain letters, numbers, hyphens, and underscores"
            )

        try:
            async with self.container.make_uow() as uow:
                repo = DatasetRepoPg(uow.session)
                exists = await repo.dataset_exists(dataset_id)

                return {
                    "dataset_id": dataset_id,
                    "exists": exists,
                    "valid": True,
                    "ready_for_upload": True,
                    "message": f"Dataset {dataset_id} is ready for document upload",
                }
        except Exception as e:
            logger.error(f"Failed to validate dataset {dataset_id}: {e}")
            raise ServiceError(
                f"Failed to validate dataset {dataset_id}",
                error_code="DATASET_VALIDATION_FAILED",
                cause=e,
            )
