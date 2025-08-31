from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Request, status

from services.assistant_service import AssistantService
from services.exceptions import ValidationError


class AssistantController:
    """Controller for Assistant API endpoints"""

    def __init__(self, request: Request):
        self.request = request
        self.assistant_service = AssistantService()

    async def create_assistant(
        self,
        name: str,
        description: Optional[str],
        knowledge_bases: List[str],
        model_settings: Dict[str, Any],
        user_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new assistant"""

        container = self.request.app.state.container
        uow = container.make_uow()

        try:
            async with uow:
                assistant = await self.assistant_service.create_assistant(
                    db_session=uow.session,
                    name=name,
                    description=description,
                    knowledge_bases=knowledge_bases,
                    model_settings=model_settings,
                    user_id=user_id,
                    system_prompt=system_prompt,
                )

                return {"code": 201, "data": assistant, "message": "Assistant created successfully"}

        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create assistant: {str(e)}",
            )

    async def get_assistant(self, assistant_id: str) -> Dict[str, Any]:
        """Get an assistant by ID"""

        container = self.request.app.state.container
        uow = container.make_uow()

        try:
            async with uow:
                assistant = await self.assistant_service.get_assistant(
                    db_session=uow.session, assistant_id=assistant_id
                )

                if not assistant:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Assistant not found",
                    )

                return {"code": 200, "data": assistant}

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get assistant: {str(e)}",
            )

    async def list_assistants(
        self,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List assistants with pagination"""

        container = self.request.app.state.container
        uow = container.make_uow()

        try:
            async with uow:
                result = await self.assistant_service.list_assistants(
                    db_session=uow.session,
                    user_id=user_id,
                    limit=limit,
                    offset=offset,
                )

                return {"code": 200, "data": result}

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list assistants: {str(e)}",
            )

    async def update_assistant(
        self,
        assistant_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        knowledge_bases: Optional[List[str]] = None,
        model_settings: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update an assistant"""

        container = self.request.app.state.container
        uow = container.make_uow()

        try:
            async with uow:
                assistant = await self.assistant_service.update_assistant(
                    db_session=uow.session,
                    assistant_id=assistant_id,
                    name=name,
                    description=description,
                    knowledge_bases=knowledge_bases,
                    model_settings=model_settings,
                    system_prompt=system_prompt,
                )

                if not assistant:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Assistant not found",
                    )

                return {"code": 200, "data": assistant, "message": "Assistant updated successfully"}

        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update assistant: {str(e)}",
            )

    async def delete_assistant(self, assistant_id: str) -> Dict[str, Any]:
        """Delete an assistant"""

        container = self.request.app.state.container
        uow = container.make_uow()

        try:
            async with uow:
                success = await self.assistant_service.delete_assistant(
                    db_session=uow.session, assistant_id=assistant_id
                )

                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Assistant not found",
                    )

                return {"code": 200, "message": "Assistant deleted successfully"}

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete assistant: {str(e)}",
            )

    async def get_assistant_with_datasets(self, assistant_id: str) -> Dict[str, Any]:
        """Get assistant with full dataset information"""

        container = self.request.app.state.container
        uow = container.make_uow()

        try:
            async with uow:
                assistant = await self.assistant_service.get_assistant_with_datasets(
                    db_session=uow.session, assistant_id=assistant_id
                )

                if not assistant:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Assistant not found",
                    )

                return {"code": 200, "data": assistant}

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get assistant details: {str(e)}",
            )
