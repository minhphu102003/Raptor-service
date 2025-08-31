import json
import time
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from fastapi.responses import StreamingResponse
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.chat import (
    ChatContextORM,
    ChatMessageORM,
    ChatSessionORM,
    ChatSessionStatus,
    MessageRole,
)
from repositories.retrieval_repo import RetrievalRepo
from services.retrieval_service import RetrievalService


class AnswerService:
    def __init__(self, *, retrieval_svc: RetrievalService, model_registry):
        self.retrieval_svc = retrieval_svc
        self.model_registry = model_registry

    async def create_chat_session(
        self,
        session: AsyncSession,
        dataset_id: str,
        title: str = "New Chat",
        user_id: Optional[str] = None,
        assistant_config: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
    ) -> ChatSessionORM:
        """Create a new chat session"""

        session_id = str(uuid4())

        chat_session = ChatSessionORM(
            session_id=session_id,
            user_id=user_id,
            dataset_id=dataset_id,
            title=title,
            status=ChatSessionStatus.active,
            assistant_config=assistant_config
            or {"model": "DeepSeek-V3", "temperature": 0.7, "max_tokens": 4000},
            system_prompt=system_prompt or "You are a helpful assistant.",
            message_count=0,
        )

        session.add(chat_session)
        await session.commit()
        return chat_session

    async def get_chat_session(
        self, session: AsyncSession, session_id: str
    ) -> Optional[ChatSessionORM]:
        """Get chat session by ID"""
        result = await session.execute(
            select(ChatSessionORM).where(
                and_(
                    ChatSessionORM.session_id == session_id,
                    ChatSessionORM.status == ChatSessionStatus.active,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_chat_history(
        self, session: AsyncSession, session_id: str, limit: int = 50
    ) -> List[ChatMessageORM]:
        """Get chat message history"""
        result = await session.execute(
            select(ChatMessageORM)
            .where(ChatMessageORM.session_id == session_id)
            .order_by(ChatMessageORM.created_at.desc())
            .limit(limit)
        )
        messages = result.scalars().all()
        return list(reversed(messages))  # Return in chronological order

    async def build_context_aware_prompt(
        self,
        session: AsyncSession,
        session_id: str,
        current_query: str,
        passages: List[dict],
        max_context_messages: int = 10,
    ) -> str:
        """Build prompt with chat context and retrieved passages"""

        # Get chat session
        chat_session = await self.get_chat_session(session, session_id)
        if not chat_session:
            return await self.build_prompt(current_query, passages)

        # Get recent messages for context
        recent_messages = await self.get_chat_history(
            session, session_id, limit=max_context_messages
        )

        # Build context from recent messages
        context_messages = []
        for msg in recent_messages[-max_context_messages:]:
            role_prefix = "User" if msg.role == MessageRole.user else "Assistant"
            context_messages.append(f"{role_prefix}: {msg.content}")

        # Build passages context
        passages_ctx = "\n\n".join(f"- {p['text']}" for p in passages)

        # Build the full prompt
        system_prompt = chat_session.system_prompt or "You are a helpful assistant."

        prompt_parts = [system_prompt]

        if context_messages:
            prompt_parts.extend(["\nPrevious conversation:", "\n".join(context_messages)])

        prompt_parts.extend(
            [
                f"\nCurrent question:\n{current_query}",
                f"\nContext (use it for grounding; quote minimally):\n{passages_ctx}",
                "\nAnswer (có trích dẫn ngắn nếu cần):",
            ]
        )

        return "\n".join(prompt_parts)

    async def save_message(
        self,
        session: AsyncSession,
        session_id: str,
        role: MessageRole,
        content: str,
        context_passages: Optional[List[dict]] = None,
        retrieval_query: Optional[str] = None,
        model_used: Optional[str] = None,
        generation_params: Optional[Dict[str, Any]] = None,
        processing_time_ms: Optional[int] = None,
    ) -> ChatMessageORM:
        """Save a chat message to database"""

        message = ChatMessageORM(
            message_id=str(uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            context_passages=context_passages,
            retrieval_query=retrieval_query,
            model_used=model_used,
            generation_params=generation_params,
            processing_time_ms=processing_time_ms,
        )

        session.add(message)

        # Update session message count
        chat_session = await self.get_chat_session(session, session_id)
        if chat_session:
            chat_session.message_count += 1

        await session.commit()
        return message

    async def build_prompt(self, query: str, passages: list[dict]) -> str:
        ctx = "\n\n".join(f"- {p['text']}" for p in passages)
        return (
            "You are a helpful assistant.\n\n"
            f"Question:\n{query}\n\n"
            "Context (use it for grounding; quote minimally):\n"
            f"{ctx}\n\n"
            "Answer (có trích dẫn ngắn nếu cần):"
        )

    async def answer_with_context(
        self, body, repo: RetrievalRepo, db_session: AsyncSession, session_id: Optional[str] = None
    ) -> Union[StreamingResponse, Dict[str, Any]]:
        """Answer with chat context support"""

        start_time = time.time()

        # Save user message if session exists
        if session_id:
            await self.save_message(db_session, session_id, MessageRole.user, body.query)

        # Retrieve relevant passages
        ret = await self.retrieval_svc.retrieve(body, repo=repo)
        if ret.get("code") != 200:
            return {"code": ret.get("code", 500), "error": "retrieval failed"}

        passages = ret.get("data", [])

        # Build context-aware prompt
        if session_id:
            prompt = await self.build_context_aware_prompt(
                db_session, session_id, body.query, passages[: body.top_k]
            )
        else:
            prompt = await self.build_prompt(body.query, passages[: body.top_k])

        # Generate response
        client = self.model_registry.get_client(body.answer_model, body)

        generation_params = {
            "temperature": body.temperature,
            "max_tokens": body.max_tokens,
            "model": body.answer_model,
        }

        if body.stream:

            async def _gen():
                response_chunks = []
                async for chunk in client.astream(
                    prompt=prompt, temperature=body.temperature, max_tokens=body.max_tokens
                ):
                    response_chunks.append(chunk)
                    yield chunk

                # Save assistant response if session exists
                if session_id:
                    full_response = "".join(response_chunks)
                    processing_time = int((time.time() - start_time) * 1000)
                    await self.save_message(
                        db_session,
                        session_id,
                        MessageRole.assistant,
                        full_response,
                        context_passages=passages[: body.top_k],
                        retrieval_query=body.query,
                        model_used=body.answer_model,
                        generation_params=generation_params,
                        processing_time_ms=processing_time,
                    )

            return StreamingResponse(_gen(), media_type="text/plain")

        # Non-streaming response
        text = await client.generate(
            prompt=prompt,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
        )

        processing_time = int((time.time() - start_time) * 1000)

        # Save assistant response if session exists
        if session_id:
            await self.save_message(
                db_session,
                session_id,
                MessageRole.assistant,
                text,
                context_passages=passages[: body.top_k],
                retrieval_query=body.query,
                model_used=body.answer_model,
                generation_params=generation_params,
                processing_time_ms=processing_time,
            )

        return {
            "answer": text,
            "model": body.answer_model,
            "top_k": body.top_k,
            "mode": body.mode,
            "passages": passages[: body.top_k],
            "session_id": session_id,
            "processing_time_ms": processing_time,
        }

    async def answer(self, body, repo: RetrievalRepo) -> Union[StreamingResponse, Dict[str, Any]]:
        """Legacy answer method for backward compatibility"""
        ret = await self.retrieval_svc.retrieve(body, repo=repo)
        if ret.get("code") != 200:
            return {"code": ret.get("code", 500), "error": "retrieval failed"}

        passages = ret.get("data", [])
        prompt = await self.build_prompt(body.query, passages[: body.top_k])

        client = self.model_registry.get_client(body.answer_model, body)
        if body.stream:

            async def _gen():
                async for chunk in client.astream(
                    prompt=prompt, temperature=body.temperature, max_tokens=body.max_tokens
                ):
                    yield chunk

            return StreamingResponse(_gen(), media_type="text/plain")

        text = await client.generate(
            prompt=prompt,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
        )
        return {
            "answer": text,
            "model": body.answer_model,
            "top_k": body.top_k,
            "mode": body.mode,
            "passages": passages[: body.top_k],
        }
