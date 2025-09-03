import json
import time
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from fastapi.responses import StreamingResponse
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.assistant import AssistantORM
from db.models.chat import (
    ChatMessageORM,
    ChatSessionORM,
    ChatSessionStatus,
    MessageRole,
)
from repositories.retrieval_repo import RetrievalRepo
from services.retrieval.retrieval_service import RetrievalService, RetrieveBody


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
        assistant_id: Optional[str] = None,
        assistant_config: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
    ) -> ChatSessionORM:
        """Create a new chat session"""

        session_id = str(uuid4())

        # If assistant_id is provided, get the assistant config from the assistant
        if assistant_id and not assistant_config:
            result = await session.execute(
                select(AssistantORM).where(AssistantORM.assistant_id == assistant_id)
            )
            assistant = result.scalar_one_or_none()
            if assistant:
                assistant_config = assistant.model_settings

        chat_session = ChatSessionORM(
            session_id=session_id,
            user_id=user_id,
            assistant_id=assistant_id,
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
        messages = list(result.scalars().all())
        messages.reverse()  # Return in chronological order
        return messages

    async def get_session_context(
        self, session: AsyncSession, session_id: str, max_context_messages: int = 6
    ) -> Dict[str, Any]:
        """
        Get session context including chat history and associated knowledge base info.

        Args:
            session: Database session
            session_id: Chat session ID
            max_context_messages: Maximum number of recent messages to include

        Returns:
            Dictionary with session context information
        """
        # Get session details
        chat_session = await self.get_chat_session(session, session_id)
        if not chat_session:
            return {"error": "Session not found"}

        # Get recent context messages
        recent_messages = await self.get_chat_history(session, session_id, max_context_messages)

        # Format messages for context
        context_messages = [
            {
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.created_at if msg.created_at else None,
            }
            for msg in recent_messages
        ]

        return {
            "session_id": session_id,
            "dataset_id": chat_session.dataset_id,
            "assistant_id": chat_session.assistant_id,
            "message_count": chat_session.message_count,
            "recent_messages": context_messages,
            "system_prompt": chat_session.system_prompt,
            "assistant_config": chat_session.assistant_config,
        }

    async def build_enhanced_context_prompt(
        self,
        session: AsyncSession,
        session_id: str,
        current_query: str,
        passages_ctx: str,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Build an enhanced context-aware prompt with additional session information.

        Args:
            session: Database session
            session_id: Chat session ID
            current_query: Current user query
            passages_ctx: Retrieved context passages
            additional_context: Additional context information

        Returns:
            Formatted prompt string
        """
        # Get session context
        session_context = await self.get_session_context(session, session_id)

        # Use system prompt from session or default
        system_prompt = session_context.get("system_prompt") or "You are a helpful assistant."

        # Format recent conversation history
        conversation_history = ""
        recent_messages = session_context.get("recent_messages", [])
        if recent_messages:
            formatted_messages = [f"{msg['role']}: {msg['content']}" for msg in recent_messages]
            conversation_history = "\n".join(formatted_messages)

        # Build the enhanced prompt
        prompt_parts = [system_prompt]

        # Add conversation history if available
        if conversation_history:
            prompt_parts.extend(["\nConversation History:", conversation_history])

        # Add additional context if provided
        if additional_context:
            prompt_parts.extend(
                [
                    "\nAdditional Context:",
                    json.dumps(additional_context, indent=2, ensure_ascii=False),
                ]
            )

        # Add current query and retrieved context
        prompt_parts.extend(
            [
                f"\nCurrent Question:\n{current_query}",
                f"\nRetrieved Context (use for grounding; quote minimally):\n{passages_ctx}",
                "\nAnswer (provide a helpful response based on the context and conversation history):",
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
        # Use 'content' if available, otherwise fallback to 'text'
        ctx = "\n\n".join(f"- {p.get('content', p.get('text', ''))}" for p in passages)
        return (
            "You are a helpful assistant.\n\n"
            f"Question:\n{query}\n\n"
            "Context (use it for grounding; quote minimally):\n"
            f"{ctx}\n\n"
            "Answer (có trích dẫn ngắn nếu cần):"
        )

    async def answer_with_context(
        self,
        body: RetrieveBody,
        *,
        repo: RetrievalRepo,
        db_session: AsyncSession,
        session_id: Optional[str] = None,
        answer_model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: Optional[bool] = None,
    ) -> Union[StreamingResponse, Dict[str, Any]]:
        """Answer with chat context support using enhanced retrieval"""

        start_time = time.time()

        # Save user message if session exists
        user_message = None
        if session_id:
            user_message = await self.save_message(
                db_session, session_id, MessageRole.user, body.query
            )

        # Retrieve relevant passages using the full capabilities of RetrievalService
        ret = await self.retrieval_svc.retrieve(body, repo=repo)
        if ret.get("code") != 200:
            return {"code": ret.get("code", 500), "error": "retrieval failed"}

        passages = ret.get("data", [])

        # Normalize passages to match frontend expectations
        normalized_passages = []
        for passage in passages:
            normalized_passage = passage.copy()
            # Map 'text' to 'content' if 'content' doesn't exist
            if "text" in passage and "content" not in passage:
                normalized_passage["content"] = passage["text"]
            normalized_passages.append(normalized_passage)

        # Build context-aware prompt with full session context
        if session_id:
            # Use enhanced prompt building with session context
            passages_text = "\n\n".join(
                [p.get("content", p.get("text", "")) for p in normalized_passages[: body.top_k]]
            )
            prompt = await self.build_enhanced_context_prompt(
                db_session, session_id, body.query, passages_text
            )
        else:
            prompt = await self.build_prompt(body.query, normalized_passages[: body.top_k])

        # Generate response
        # Use provided parameters or defaults
        model_to_use = answer_model or "DeepSeek-V3"
        temp_to_use = temperature or 0.7
        tokens_to_use = max_tokens or 4000
        stream_to_use = stream if stream is not None else False

        client = self.model_registry.get_client(model_to_use, body)

        generation_params = {
            "temperature": temp_to_use,
            "max_tokens": tokens_to_use,
            "model": model_to_use,
        }

        if stream_to_use:

            async def _gen():
                response_chunks = []
                async for chunk in client.astream(
                    prompt=prompt, temperature=temp_to_use, max_tokens=tokens_to_use
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
                        context_passages=normalized_passages[: body.top_k],
                        retrieval_query=body.query,
                        model_used=model_to_use,
                        generation_params=generation_params,
                        processing_time_ms=processing_time,
                    )

            return StreamingResponse(_gen(), media_type="text/plain")

        # Non-streaming response
        text = await client.generate(
            prompt=prompt,
            temperature=temp_to_use,
            max_tokens=tokens_to_use,
        )

        processing_time = int((time.time() - start_time) * 1000)

        # Save assistant response if session exists
        assistant_message = None
        if session_id:
            assistant_message = await self.save_message(
                db_session,
                session_id,
                MessageRole.assistant,
                text,
                context_passages=normalized_passages[: body.top_k],
                retrieval_query=body.query,
                model_used=model_to_use,
                generation_params=generation_params,
                processing_time_ms=processing_time,
            )

        # Return proper response format for frontend
        response_data = {
            "answer": text,
            "model": model_to_use,
            "top_k": body.top_k,
            "mode": body.mode,
            "passages": normalized_passages[: body.top_k],
            "session_id": session_id,
            "processing_time_ms": processing_time,
        }

        # If we have saved messages, include their data for the frontend
        if user_message and assistant_message:
            response_data["user_message"] = {
                "message_id": user_message.message_id,
                "session_id": user_message.session_id,
                "role": user_message.role.value,
                "content": user_message.content,
                "created_at": user_message.created_at,
            }
            response_data["assistant_message"] = {
                "message_id": assistant_message.message_id,
                "session_id": assistant_message.session_id,
                "role": assistant_message.role.value,
                "content": assistant_message.content,
                "context_passages": assistant_message.context_passages,
                "model_used": assistant_message.model_used,
                "processing_time_ms": assistant_message.processing_time_ms,
                "created_at": assistant_message.created_at,
            }

        return response_data

    async def answer(self, body, repo: RetrievalRepo) -> Union[StreamingResponse, Dict[str, Any]]:
        """Legacy answer method for backward compatibility"""
        ret = await self.retrieval_svc.retrieve(body, repo=repo)
        if ret.get("code") != 200:
            return {"code": ret.get("code", 500), "error": "retrieval failed"}

        passages = ret.get("data", [])

        # Normalize passages to match frontend expectations
        normalized_passages = []
        for passage in passages:
            normalized_passage = passage.copy()
            # Map 'text' to 'content' if 'content' doesn't exist
            if "text" in passage and "content" not in passage:
                normalized_passage["content"] = passage["text"]
            normalized_passages.append(normalized_passage)

        prompt = await self.build_prompt(body.query, normalized_passages[: body.top_k])

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
            "passages": normalized_passages[: body.top_k],
        }

    async def summarize_conversation_context(
        self, session: AsyncSession, session_id: str, max_messages: int = 10
    ) -> Dict[str, Any]:
        """
        Create a summary of the conversation context for better understanding.

        Args:
            session: Database session
            session_id: Chat session ID
            max_messages: Maximum number of messages to include in summary

        Returns:
            Dictionary with conversation summary
        """
        # Get session context
        context = await self.get_session_context(session, session_id, max_messages)

        if "error" in context:
            return context

        # Extract key information
        recent_messages = context.get("recent_messages", [])
        message_count = context.get("message_count", 0)
        assistant_config = context.get("assistant_config", {})

        # Identify conversation topics from recent messages
        user_messages = [msg for msg in recent_messages if msg["role"] == "user"]
        topics = []
        if user_messages:
            # Simple topic extraction - in a real implementation, you might use NLP
            topics = list(
                set(
                    [
                        msg["content"][:30] + "..." if len(msg["content"]) > 30 else msg["content"]
                        for msg in user_messages[-3:]
                    ]
                )
            )  # Last 3 user messages

        return {
            "session_id": session_id,
            "message_count": message_count,
            "recent_message_count": len(recent_messages),
            "topics_discussed": topics,
            "model_used": assistant_config.get("model", "unknown"),
            "conversation_length": "long"
            if message_count > 10
            else "medium"
            if message_count > 5
            else "short",
        }
