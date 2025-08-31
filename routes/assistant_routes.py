from typing import Annotated, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from controllers.assistant_controller import AssistantController

router = APIRouter()


# Request/Response Models
class ModelSettings(BaseModel):
    model: str = Field(..., description="Model name (e.g., 'gpt-4o', 'DeepSeek-V3')")
    temperature: float = Field(
        0.7, ge=0.0, le=2.0, description="Temperature for response generation"
    )
    topP: float = Field(1.0, ge=0.0, le=1.0, description="Top P for nucleus sampling")
    presencePenalty: float = Field(0.0, ge=-2.0, le=2.0, description="Presence penalty")
    frequencyPenalty: float = Field(0.0, ge=-2.0, le=2.0, description="Frequency penalty")


class CreateAssistantRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, description="Assistant name")
    description: Optional[str] = Field(None, max_length=500, description="Assistant description")
    knowledge_bases: List[str] = Field(
        ..., description="List of dataset/knowledge base IDs (at least one required)"
    )
    model_settings: ModelSettings = Field(..., description="Model configuration")
    user_id: Optional[str] = Field(None, description="User ID (for future user management)")
    system_prompt: Optional[str] = Field(None, max_length=2000, description="Custom system prompt")


class UpdateAssistantRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100, description="Assistant name")
    description: Optional[str] = Field(None, max_length=500, description="Assistant description")
    knowledge_bases: Optional[List[str]] = Field(
        None, description="List of dataset/knowledge base IDs (at least one required)"
    )
    model_settings: Optional[ModelSettings] = Field(None, description="Model configuration")
    system_prompt: Optional[str] = Field(None, max_length=2000, description="Custom system prompt")


@router.post("/assistants", summary="Create new assistant")
async def create_assistant(request: Request, body: CreateAssistantRequest):
    """
    Create a new AI assistant with specified configuration.

    Args:
        body: Assistant creation parameters

    Returns:
        Created assistant information
    """
    controller = AssistantController(request)

    return await controller.create_assistant(
        name=body.name,
        description=body.description,
        knowledge_bases=body.knowledge_bases,
        model_settings=body.model_settings.dict(),
        user_id=body.user_id,
        system_prompt=body.system_prompt,
    )


@router.get("/assistants", summary="List assistants")
async def list_assistants(
    request: Request,
    user_id: Annotated[Optional[str], Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """
    List assistants with optional filtering and pagination.

    Args:
        user_id: Filter by user ID
        limit: Maximum number of assistants to return
        offset: Number of assistants to skip

    Returns:
        List of assistants with pagination info
    """
    controller = AssistantController(request)

    return await controller.list_assistants(
        user_id=user_id,
        limit=limit,
        offset=offset,
    )


@router.get("/assistants/{assistant_id}", summary="Get assistant")
async def get_assistant(assistant_id: str, request: Request):
    """
    Get details of a specific assistant.

    Args:
        assistant_id: The assistant ID

    Returns:
        Assistant details
    """
    controller = AssistantController(request)

    return await controller.get_assistant(assistant_id)


@router.get("/assistants/{assistant_id}/details", summary="Get assistant with dataset details")
async def get_assistant_with_datasets(assistant_id: str, request: Request):
    """
    Get assistant details including full dataset information.

    Args:
        assistant_id: The assistant ID

    Returns:
        Assistant details with dataset information
    """
    controller = AssistantController(request)

    return await controller.get_assistant_with_datasets(assistant_id)


@router.put("/assistants/{assistant_id}", summary="Update assistant")
async def update_assistant(assistant_id: str, request: Request, body: UpdateAssistantRequest):
    """
    Update an assistant's configuration.

    Args:
        assistant_id: The assistant ID
        body: Update parameters

    Returns:
        Updated assistant information
    """
    controller = AssistantController(request)

    model_settings = body.model_settings.dict() if body.model_settings else None

    return await controller.update_assistant(
        assistant_id=assistant_id,
        name=body.name,
        description=body.description,
        knowledge_bases=body.knowledge_bases,
        model_settings=model_settings,
        system_prompt=body.system_prompt,
    )


@router.delete("/assistants/{assistant_id}", summary="Delete assistant")
async def delete_assistant(assistant_id: str, request: Request):
    """
    Delete (soft delete) an assistant.

    Args:
        assistant_id: The assistant ID

    Returns:
        Deletion confirmation
    """
    controller = AssistantController(request)

    return await controller.delete_assistant(assistant_id)
