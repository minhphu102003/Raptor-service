from typing import Annotated

from fastapi import APIRouter, Query, Request, status

from controllers.dataset_controller import DatasetController

router = APIRouter()


@router.get("/", summary="List all datasets")
async def list_datasets(request: Request):
    """
    Get a list of all available datasets/knowledge bases.

    Returns:
        - List of datasets with metadata (id, name, description, document_count, etc.)
    """
    controller = DatasetController(request)
    return await controller.list_datasets()


@router.get("/{dataset_id}", summary="Get dataset details")
async def get_dataset(dataset_id: str, request: Request):
    """
    Get detailed information about a specific dataset.

    Args:
        dataset_id: The unique identifier of the dataset

    Returns:
        - Dataset details including document count, chunk count, embedding count, etc.
    """
    controller = DatasetController(request)
    return await controller.get_dataset(dataset_id)


@router.get("/{dataset_id}/documents", summary="List documents in dataset")
async def get_dataset_documents(
    dataset_id: str,
    request: Request,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """
    Get a paginated list of documents in a specific dataset.

    Args:
        dataset_id: The unique identifier of the dataset
        page: Page number (starts from 1)
        page_size: Number of documents per page (max 100)

    Returns:
        - List of documents with pagination metadata
    """
    controller = DatasetController(request)
    return await controller.get_dataset_documents(dataset_id, page, page_size)


@router.get("/{dataset_id}/statistics", summary="Get dataset statistics")
async def get_dataset_statistics(dataset_id: str, request: Request):
    """
    Get comprehensive statistics for a dataset.

    Args:
        dataset_id: The unique identifier of the dataset

    Returns:
        - Statistical information including token counts, processing status, etc.
    """
    controller = DatasetController(request)
    return await controller.get_dataset_statistics(dataset_id)


@router.post("/{dataset_id}/validate", summary="Validate dataset for upload")
async def validate_dataset(dataset_id: str, request: Request):
    """
    Validate if a dataset ID is valid and ready for document upload.

    Args:
        dataset_id: The dataset ID to validate

    Returns:
        - Validation result with details about the dataset
    """
    controller = DatasetController(request)
    return await controller.validate_dataset(dataset_id)


@router.head("/{dataset_id}", summary="Check if dataset exists")
async def check_dataset_exists(dataset_id: str, request: Request):
    """
    Check if a dataset exists (returns 200 if exists, 404 if not).

    Args:
        dataset_id: The unique identifier of the dataset

    Returns:
        - HTTP status code only (no body)
    """
    controller = DatasetController(request)
    return await controller.check_dataset_exists(dataset_id)


@router.delete("/{dataset_id}", summary="Delete dataset")
async def delete_dataset(dataset_id: str, request: Request):
    """
    Delete a dataset and all its associated data (documents, chunks, embeddings, trees).

    **Warning:** This operation cannot be undone!

    Args:
        dataset_id: The unique identifier of the dataset to delete

    Returns:
        - Deletion confirmation with statistics
    """
    controller = DatasetController(request)
    return await controller.delete_dataset(dataset_id)