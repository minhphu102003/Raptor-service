from typing import List, Optional
from uuid import uuid4

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.assistant import AssistantORM, AssistantStatus


class AssistantRepoPg:
    """PostgreSQL repository for Assistant operations"""

    async def create_assistant(
        self,
        db_session: AsyncSession,
        name: str,
        description: Optional[str],
        knowledge_bases: List[str],
        model_settings: dict,
        user_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> AssistantORM:
        """Create a new assistant"""

        assistant_id = str(uuid4())

        assistant = AssistantORM(
            assistant_id=assistant_id,
            user_id=user_id,
            name=name,
            description=description,
            knowledge_bases=knowledge_bases,
            model_settings=model_settings,
            system_prompt=system_prompt,
            status=AssistantStatus.active,
        )

        db_session.add(assistant)
        await db_session.commit()
        await db_session.refresh(assistant)

        return assistant

    async def get_assistant_by_id(
        self, db_session: AsyncSession, assistant_id: str
    ) -> Optional[AssistantORM]:
        """Get an assistant by ID"""

        result = await db_session.execute(
            select(AssistantORM).where(
                and_(
                    AssistantORM.assistant_id == assistant_id,
                    AssistantORM.status == AssistantStatus.active,
                )
            )
        )

        return result.scalar_one_or_none()

    async def list_assistants(
        self,
        db_session: AsyncSession,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AssistantORM]:
        """List assistants with optional filtering"""

        query = select(AssistantORM).where(AssistantORM.status == AssistantStatus.active)

        if user_id:
            query = query.where(AssistantORM.user_id == user_id)

        query = query.order_by(desc(AssistantORM.created_at)).limit(limit).offset(offset)

        result = await db_session.execute(query)
        return list(result.scalars().all())

    async def update_assistant(
        self,
        db_session: AsyncSession,
        assistant_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        knowledge_bases: Optional[List[str]] = None,
        model_settings: Optional[dict] = None,
        system_prompt: Optional[str] = None,
    ) -> Optional[AssistantORM]:
        """Update an assistant"""

        result = await db_session.execute(
            select(AssistantORM).where(
                and_(
                    AssistantORM.assistant_id == assistant_id,
                    AssistantORM.status == AssistantStatus.active,
                )
            )
        )

        assistant = result.scalar_one_or_none()
        if not assistant:
            return None

        # Update fields if provided
        if name is not None:
            assistant.name = name
        if description is not None:
            assistant.description = description
        if knowledge_bases is not None:
            assistant.knowledge_bases = knowledge_bases
        if model_settings is not None:
            assistant.model_settings = model_settings
        if system_prompt is not None:
            assistant.system_prompt = system_prompt

        await db_session.commit()
        await db_session.refresh(assistant)

        return assistant

    async def delete_assistant(self, db_session: AsyncSession, assistant_id: str) -> bool:
        """Soft delete an assistant"""

        result = await db_session.execute(
            select(AssistantORM).where(
                and_(
                    AssistantORM.assistant_id == assistant_id,
                    AssistantORM.status == AssistantStatus.active,
                )
            )
        )

        assistant = result.scalar_one_or_none()
        if not assistant:
            return False

        assistant.status = AssistantStatus.deleted
        await db_session.commit()

        return True

    async def count_assistants(
        self, db_session: AsyncSession, user_id: Optional[str] = None
    ) -> int:
        """Count total assistants"""

        query = select(AssistantORM).where(AssistantORM.status == AssistantStatus.active)

        if user_id:
            query = query.where(AssistantORM.user_id == user_id)

        result = await db_session.execute(query)
        return len(list(result.scalars().all()))
