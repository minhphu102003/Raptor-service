from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.assistant_repo_pg import AssistantRepoPg
from repositories.dataset_repo_pg import DatasetRepoPg
from services.shared.exceptions import ValidationError


class AssistantService:
    """Service for managing AI assistants"""

    def __init__(self):
        self.assistant_repo = AssistantRepoPg()

    async def create_assistant(
        self,
        db_session: AsyncSession,
        name: str,
        description: Optional[str],
        knowledge_bases: List[str],
        model_settings: Dict[str, Any],
        user_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new assistant with validation"""

        # Validate input
        if not name or not name.strip():
            raise ValidationError("Assistant name is required")

        if len(name.strip()) < 3:
            raise ValidationError("Assistant name must be at least 3 characters long")

        if len(name.strip()) > 100:
            raise ValidationError("Assistant name must be less than 100 characters")

        if not knowledge_bases:
            raise ValidationError("At least one knowledge base must be selected")

        # Validate knowledge bases exist
        for kb_id in knowledge_bases:
            dataset_repo = DatasetRepoPg(db_session)
            dataset_exists = await dataset_repo.dataset_exists(kb_id)
            if not dataset_exists:
                raise ValidationError(f"Knowledge base with ID {kb_id} not found")

        # Validate model settings
        required_model_fields = [
            "model",
            "temperature",
            "topP",
            "presencePenalty",
            "frequencyPenalty",
        ]
        for field in required_model_fields:
            if field not in model_settings:
                raise ValidationError(f"Model setting '{field}' is required")

        # Validate temperature range
        if not (0.0 <= model_settings["temperature"] <= 2.0):
            raise ValidationError("Temperature must be between 0.0 and 2.0")

        # Validate topP range
        if not (0.0 <= model_settings["topP"] <= 1.0):
            raise ValidationError("Top P must be between 0.0 and 1.0")

        # Create assistant
        assistant = await self.assistant_repo.create_assistant(
            db_session=db_session,
            name=name.strip(),
            description=description.strip() if description else None,
            knowledge_bases=knowledge_bases,
            model_settings=model_settings,
            user_id=user_id,
            system_prompt=system_prompt,
        )

        return assistant.to_dict()

    async def get_assistant(
        self, db_session: AsyncSession, assistant_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get an assistant by ID"""

        assistant = await self.assistant_repo.get_assistant_by_id(db_session, assistant_id)
        if not assistant:
            return None

        return assistant.to_dict()

    async def list_assistants(
        self,
        db_session: AsyncSession,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List assistants with pagination"""

        assistants = await self.assistant_repo.list_assistants(
            db_session, user_id=user_id, limit=limit, offset=offset
        )

        total_count = await self.assistant_repo.count_assistants(db_session, user_id=user_id)

        return {
            "assistants": [assistant.to_dict() for assistant in assistants],
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(assistants) < total_count,
        }

    async def update_assistant(
        self,
        db_session: AsyncSession,
        assistant_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        knowledge_bases: Optional[List[str]] = None,
        model_settings: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update an assistant with validation"""

        # Validate name if provided
        if name is not None:
            if not name.strip():
                raise ValidationError("Assistant name cannot be empty")
            if len(name.strip()) < 3:
                raise ValidationError("Assistant name must be at least 3 characters long")
            if len(name.strip()) > 100:
                raise ValidationError("Assistant name must be less than 100 characters")

        # Validate knowledge bases if provided
        if knowledge_bases is not None:
            if not knowledge_bases:
                raise ValidationError("At least one knowledge base must be selected")

            dataset_repo = DatasetRepoPg(db_session)
            for kb_id in knowledge_bases:
                dataset_exists = await dataset_repo.dataset_exists(kb_id)
                if not dataset_exists:
                    raise ValidationError(f"Knowledge base with ID {kb_id} not found")

        # Validate model settings if provided
        if model_settings is not None:
            if "temperature" in model_settings:
                if not (0.0 <= model_settings["temperature"] <= 2.0):
                    raise ValidationError("Temperature must be between 0.0 and 2.0")

            if "topP" in model_settings:
                if not (0.0 <= model_settings["topP"] <= 1.0):
                    raise ValidationError("Top P must be between 0.0 and 1.0")

        # Update assistant
        assistant = await self.assistant_repo.update_assistant(
            db_session=db_session,
            assistant_id=assistant_id,
            name=name.strip() if name else None,
            description=description.strip() if description else None,
            knowledge_bases=knowledge_bases,
            model_settings=model_settings,
            system_prompt=system_prompt,
        )

        if not assistant:
            return None

        return assistant.to_dict()

    async def delete_assistant(self, db_session: AsyncSession, assistant_id: str) -> bool:
        """Delete an assistant"""

        return await self.assistant_repo.delete_assistant(db_session, assistant_id)

    async def get_assistant_with_datasets(
        self, db_session: AsyncSession, assistant_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get assistant with full dataset information"""

        assistant = await self.assistant_repo.get_assistant_by_id(db_session, assistant_id)
        if not assistant:
            return None

        # Get detailed dataset information
        datasets = []
        dataset_repo = DatasetRepoPg(db_session)
        for kb_id in assistant.knowledge_bases:
            dataset_info = await dataset_repo.get_dataset_info(kb_id)
            if dataset_info:
                datasets.append(
                    {
                        "id": dataset_info["id"],
                        "name": dataset_info["name"],
                        "description": dataset_info["description"],
                        "doc_count": dataset_info["document_count"],
                        "created_at": dataset_info["created_at"],
                    }
                )

        assistant_dict = assistant.to_dict()
        assistant_dict["datasets"] = datasets

        return assistant_dict
