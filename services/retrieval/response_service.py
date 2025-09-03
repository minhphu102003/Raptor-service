import time
from typing import Any, Dict, List, Optional, Union

from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.chat import MessageRole
from repositories.retrieval_repo import RetrievalRepo
from services.retrieval.retrieval_service import RetrieveBody


class ResponseService:
    def __init__(self, retrieval_svc, model_registry, message_service, prompt_service):
        self.retrieval_svc = retrieval_svc
        self.model_registry = model_registry
        self.message_service = message_service
        self.prompt_service = prompt_service

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
        start_time = time.time()

        user_message = None
        if session_id:
            user_message = await self.message_service.save_message(
                db_session, session_id, MessageRole.user, body.query
            )

        ret = await self.retrieval_svc.retrieve(body, repo=repo)
        if ret.get("code") != 200:
            return {"code": ret.get("code", 500), "error": "retrieval failed"}

        passages = ret.get("data", [])

        normalized_passages = []
        for passage in passages:
            normalized_passage = passage.copy()
            if "text" in passage and "content" not in passage:
                normalized_passage["content"] = passage["text"]
            normalized_passages.append(normalized_passage)

        if session_id:
            # Get session context
            from services.retrieval.answer_service import AnswerService

            answer_service = AnswerService(
                retrieval_svc=self.retrieval_svc, model_registry=self.model_registry
            )
            session_context = await answer_service.get_session_context(db_session, session_id)

            passages_text = "\n\n".join(
                [p.get("content", p.get("text", "")) for p in normalized_passages[: body.top_k]]
            )
            prompt = await self.prompt_service.build_enhanced_context_prompt(
                session_context, body.query, passages_text
            )
        else:
            prompt = await self.prompt_service.build_prompt(
                body.query, normalized_passages[: body.top_k]
            )

        model_to_use = answer_model or "DeepSeek-V3"
        temp_to_use = temperature or 0.7
        tokens_to_use = max_tokens or 8000
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

                if session_id:
                    full_response = "".join(response_chunks)
                    processing_time = int((time.time() - start_time) * 1000)
                    await self.message_service.save_message(
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

        text = await client.generate(
            prompt=prompt,
            temperature=temp_to_use,
            max_tokens=tokens_to_use,
        )

        processing_time = int((time.time() - start_time) * 1000)

        assistant_message = None
        if session_id:
            assistant_message = await self.message_service.save_message(
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

        response_data = {
            "answer": text,
            "model": model_to_use,
            "top_k": body.top_k,
            "mode": body.mode,
            "passages": normalized_passages[: body.top_k],
            "session_id": session_id,
            "processing_time_ms": processing_time,
        }

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
        ret = await self.retrieval_svc.retrieve(body, repo=repo)
        if ret.get("code") != 200:
            return {"code": ret.get("code", 500), "error": "retrieval failed"}

        passages = ret.get("data", [])

        normalized_passages = []
        for passage in passages:
            normalized_passage = passage.copy()
            if "text" in passage and "content" not in passage:
                normalized_passage["content"] = passage["text"]
            normalized_passages.append(normalized_passage)

        prompt = await self.prompt_service.build_prompt(
            body.query, normalized_passages[: body.top_k]
        )

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
