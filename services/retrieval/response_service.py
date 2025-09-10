import json
import logging
import time
from typing import Any, Dict, List, Optional, Union

from fastapi.responses import StreamingResponse

# Add Langfuse imports
from langfuse import get_client, observe
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.chat import MessageRole
from repositories.retrieval_repo import RetrievalRepo
from services.retrieval.retrieval_service import RetrieveBody

logger = logging.getLogger("raptor.retrieve.response")


def _ms_since(t0: float) -> float:
    return round((time.perf_counter() - t0) * 1000.0, 1)


class ResponseService:
    def __init__(self, retrieval_svc, model_registry, message_service, prompt_service):
        self.retrieval_svc = retrieval_svc
        self.model_registry = model_registry
        self.message_service = message_service
        self.prompt_service = prompt_service

    @observe(name="answer_with_context", as_type="generation")
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
        logger.info(f"Starting answer_with_context for query: {body.query}")

        # Get the current Langfuse trace
        langfuse = get_client()

        user_message = None
        if session_id:
            logger.debug(f"Saving user message for session: {session_id}")
            user_message = await self.message_service.save_message(
                db_session, session_id, MessageRole.user, body.query
            )

        logger.debug("Starting retrieval process")
        ret = await self.retrieval_svc.retrieve(body, repo=repo)
        if ret.get("code") != 200:
            logger.error(f"Retrieval failed with code: {ret.get('code', 500)}")
            return {"code": ret.get("code", 500), "error": "retrieval failed"}

        passages = ret.get("data", [])
        logger.debug(f"Retrieved {len(passages)} passages")

        normalized_passages = []
        for passage in passages:
            normalized_passage = passage.copy()
            if "text" in passage and "content" not in passage:
                normalized_passage["content"] = passage["text"]
            normalized_passages.append(normalized_passage)

        if session_id:
            # Get session context
            logger.debug(f"Building enhanced context prompt for session: {session_id}")
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
            logger.debug("Building standard prompt")
            prompt = await self.prompt_service.build_prompt(
                body.query, normalized_passages[: body.top_k]
            )

        model_to_use = answer_model or "DeepSeek-V3"
        temp_to_use = temperature or 0.7
        tokens_to_use = max_tokens or 8000
        stream_to_use = stream if stream is not None else False

        logger.debug(
            f"Using model: {model_to_use}, temperature: {temp_to_use}, max_tokens: {tokens_to_use}"
        )

        client = self.model_registry.get_client(model_to_use, body)

        generation_params = {
            "temperature": temp_to_use,
            "max_tokens": tokens_to_use,
            "model": model_to_use,
        }

        # Update trace with model information
        langfuse.update_current_span(
            input=body.query,
            metadata={
                "model": model_to_use,
                "temperature": temp_to_use,
                "max_tokens": tokens_to_use,
                "top_k": body.top_k,
                "mode": body.mode,
            },
        )

        if stream_to_use:
            logger.debug("Streaming response enabled")

            async def _gen():
                logger.debug("Starting streaming generation")
                response_chunks = []
                # Track LLM generation time specifically
                llm_start_time = time.perf_counter()
                async for chunk in client.astream(
                    prompt=prompt, temperature=temp_to_use, max_tokens=tokens_to_use
                ):
                    response_chunks.append(chunk)
                    yield chunk

                llm_time = _ms_since(llm_start_time)
                logger.info(
                    f"LLM streaming generation completed in {llm_time}ms",
                    extra={"span": "llm.streaming", "ms": llm_time},
                )

                if session_id:
                    full_response = "".join(response_chunks)
                    processing_time = int((time.time() - start_time) * 1000)
                    logger.debug(f"Saving assistant message for session: {session_id}")
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

                    # Send context_passages in the final chunk as JSON
                    final_data = {
                        "answer": full_response,
                        "model": model_to_use,
                        "top_k": body.top_k,
                        "mode": body.mode,
                        "passages": normalized_passages[: body.top_k],
                        "session_id": session_id,
                        "processing_time_ms": processing_time,
                        "llm_generation_time_ms": llm_time,
                    }
                    yield f"\n{json.dumps(final_data, ensure_ascii=False)}"

            return StreamingResponse(_gen(), media_type="text/plain")

        logger.debug("Starting non-streaming generation")
        # Track LLM generation time specifically
        llm_start_time = time.perf_counter()
        text = await client.generate(
            prompt=prompt,
            temperature=temp_to_use,
            max_tokens=tokens_to_use,
        )
        llm_time = _ms_since(llm_start_time)
        logger.info(
            f"LLM generation completed in {llm_time}ms",
            extra={"span": "llm.generation", "ms": llm_time},
        )

        processing_time = int((time.time() - start_time) * 1000)
        logger.debug(f"Generation completed in {processing_time}ms")

        assistant_message = None
        if session_id:
            logger.debug(f"Saving assistant message for session: {session_id}")
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
            "llm_generation_time_ms": llm_time,  # Include LLM time in response
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

        logger.info(f"Answer with context completed in {processing_time}ms")
        return response_data

    async def answer(self, body, repo: RetrievalRepo) -> Union[StreamingResponse, Dict[str, Any]]:
        logger.info(f"Starting answer for query: {body.query}")
        start_time = time.time()

        ret = await self.retrieval_svc.retrieve(body, repo=repo)
        if ret.get("code") != 200:
            logger.error(f"Retrieval failed with code: {ret.get('code', 500)}")
            return {"code": ret.get("code", 500), "error": "retrieval failed"}

        passages = ret.get("data", [])
        logger.debug(f"Retrieved {len(passages)} passages")

        normalized_passages = []
        for passage in passages:
            normalized_passage = passage.copy()
            if "text" in passage and "content" not in passage:
                normalized_passage["content"] = passage["text"]
            normalized_passages.append(normalized_passage)

        logger.debug("Building prompt")
        prompt = await self.prompt_service.build_prompt(
            body.query, normalized_passages[: body.top_k]
        )

        client = self.model_registry.get_client(body.answer_model, body)

        logger.debug(f"Using model: {body.answer_model}")

        if body.stream:
            logger.debug("Streaming response enabled")

            async def _gen():
                logger.debug("Starting streaming generation")
                response_chunks = []
                # Track LLM generation time specifically
                llm_start_time = time.perf_counter()
                async for chunk in client.astream(
                    prompt=prompt, temperature=body.temperature, max_tokens=body.max_tokens
                ):
                    response_chunks.append(chunk)
                    yield chunk

                llm_time = _ms_since(llm_start_time)
                logger.info(
                    f"LLM streaming generation completed in {llm_time}ms",
                    extra={"span": "llm.streaming", "ms": llm_time},
                )

                # Send context_passages in the final chunk as JSON
                final_data = {
                    "answer": "".join(response_chunks),
                    "model": body.answer_model,
                    "top_k": body.top_k,
                    "mode": body.mode,
                    "passages": normalized_passages[: body.top_k],
                    "llm_generation_time_ms": llm_time,
                }
                yield f"\n{json.dumps(final_data, ensure_ascii=False)}"

            return StreamingResponse(_gen(), media_type="text/plain")

        logger.debug("Starting non-streaming generation")
        # Track LLM generation time specifically
        llm_start_time = time.perf_counter()
        text = await client.generate(
            prompt=prompt,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
        )
        llm_time = _ms_since(llm_start_time)
        logger.info(
            f"LLM generation completed in {llm_time}ms",
            extra={"span": "llm.generation", "ms": llm_time},
        )

        processing_time = int((time.time() - start_time) * 1000)
        logger.debug(f"Generation completed in {processing_time}ms")

        result = {
            "answer": text,
            "model": body.answer_model,
            "top_k": body.top_k,
            "mode": body.mode,
            "passages": normalized_passages[: body.top_k],
            "llm_generation_time_ms": llm_time,  # Include LLM time in response
        }

        logger.info(f"Answer completed in {processing_time}ms")
        return result
