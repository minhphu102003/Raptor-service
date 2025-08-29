from functools import wraps
import logging
from typing import Any, Callable, Optional

from fastapi import HTTPException, Request, status

from services.dataset_service import DatasetService
from services.exceptions import ServiceError, ValidationError

logger = logging.getLogger(__name__)


def handle_service_errors(func: Callable) -> Callable:
    """Decorator to handle common service errors"""

    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation error in {func.__name__}: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except ServiceError as e:
            logger.error(f"Service error in {func.__name__}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error"
            )

    return wrapper


class DatasetController:
    """Controller for dataset/knowledge base HTTP endpoints"""

    def __init__(self, request: Request):
        self.request = request
        self.container = request.app.state.container
        self.service = DatasetService(self.container)

    @handle_service_errors
    async def list_datasets(self):
        """Handle GET /datasets - list all datasets"""
        datasets = await self.service.list_datasets()
        return {"datasets": datasets, "total": len(datasets)}

    @handle_service_errors
    async def get_dataset(self, dataset_id: str):
        """Handle GET /datasets/{dataset_id} - get dataset details"""
        dataset = await self.service.get_dataset_details(dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset '{dataset_id}' not found"
            )
        return dataset

    @handle_service_errors
    async def get_dataset_documents(self, dataset_id: str, page: int = 1, page_size: int = 20):
        """Handle GET /datasets/{dataset_id}/documents - get documents in dataset"""
        result = await self.service.get_dataset_documents(
            dataset_id=dataset_id, page=page, page_size=page_size
        )
        return result

    @handle_service_errors
    async def delete_dataset(self, dataset_id: str):
        """Handle DELETE /datasets/{dataset_id} - delete dataset"""
        result = await self.service.delete_dataset(dataset_id)
        return {"message": f"Dataset '{dataset_id}' deleted successfully", "details": result}

    @handle_service_errors
    async def get_dataset_statistics(self, dataset_id: str):
        """Handle GET /datasets/{dataset_id}/statistics - get dataset statistics"""
        stats = await self.service.get_dataset_statistics(dataset_id)
        return stats

    @handle_service_errors
    async def validate_dataset(self, dataset_id: str):
        """Handle POST /datasets/{dataset_id}/validate - validate dataset for upload"""
        result = await self.service.validate_dataset_for_upload(dataset_id)
        return result

    @handle_service_errors
    async def check_dataset_exists(self, dataset_id: str):
        """Handle HEAD /datasets/{dataset_id} - check if dataset exists"""
        exists = await self.service.dataset_exists(dataset_id)
        if not exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset '{dataset_id}' not found"
            )
        return {"exists": True}
