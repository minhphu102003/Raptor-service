import time

from fastapi import HTTPException, Request, status
from fastapi.responses import StreamingResponse

from controllers.dataset_controller import DatasetController
from db.models.chat import MessageRole
from dtos.chat_dto import ChatMessageRequest, EnhancedChatMessageRequest
from repositories.retrieval_repo import RetrievalRepo
from services import AnswerService, ChatService


class ChatMessageController:
    """Controller for chat message HTTP endpoints"""

    def __init__(self, request: Request, chat_service: ChatService, answer_service: AnswerService):
        self.request = request
        self.container = request.app.state.container
        self._chat = chat_service
        self._answer = answer_service

    async def send_chat_message(self, body: ChatMessageRequest):
        """Send a message and get AI response with chat context."""
        uow = self.container.make_uow()
        async with uow:
            repo = RetrievalRepo(uow)

            # Validate dataset
            dataset_controller = DatasetController(self.request)
            try:
                await dataset_controller.validate_dataset(body.dataset_id)
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid dataset ID: {body.dataset_id}",
                )

            # If session_id provided, validate it exists
            if body.session_id:
                session_data = await self._chat.get_session(uow.session, body.session_id)
                if not session_data:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found"
                    )

            # Create a RetrieveBody object from ChatMessageRequest
            from services.retrieval import RetrieveBody

            retrieve_body = RetrieveBody(
                dataset_id=body.dataset_id,
                query=body.query,
                mode="collapsed" if body.mode == "tree" else "traversal",
                top_k=body.top_k,
                expand_k=body.expand_k,
                levels_cap=0,  # Default value
                use_reranker=False,  # Default value
                reranker_model=None,  # Default value
                byok_voyage_api_key=None,  # Default value
            )

            # Get response with context using the retrieve_body and additional parameters
            result = await self._answer.answer_with_context(
                retrieve_body,
                repo=repo,
                db_session=uow.session,
                session_id=body.session_id,
                answer_model=body.answer_model,
                temperature=body.temperature,
                max_tokens=body.max_tokens,
                stream=body.stream,
            )

            return result

    async def send_enhanced_chat_message(self, body: EnhancedChatMessageRequest):
        """Send a message and get AI response with enhanced context awareness."""
        uow = self.container.make_uow()
        async with uow:
            repo = RetrievalRepo(uow)

            # Validate dataset
            dataset_controller = DatasetController(self.request)
            try:
                await dataset_controller.validate_dataset(body.dataset_id)
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid dataset ID: {body.dataset_id}",
                )

            # If session_id provided, validate it exists
            if body.session_id:
                session_data = await self._chat.get_session(uow.session, body.session_id)
                if not session_data:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found"
                    )

            # Create a RetrieveBody object from EnhancedChatMessageRequest
            from services.retrieval import RetrieveBody

            retrieve_body = RetrieveBody(
                dataset_id=body.dataset_id,
                query=body.query,
                mode="collapsed" if body.mode == "tree" else "traversal",
                top_k=body.top_k,
                expand_k=body.expand_k,
                levels_cap=0,  # Default value
                use_reranker=False,  # Default value
                reranker_model=None,  # Default value
                byok_voyage_api_key=None,  # Default value
            )

            # Retrieve relevant passages using the full capabilities of RetrievalService
            ret = await self._answer.retrieval_svc.retrieve(retrieve_body, repo=repo)
            if ret.get("code") != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve context",
                )

            passages = ret.get("data", [])
            # Use 'content' if available, otherwise fallback to 'text'
            passages_ctx = "\n\n".join(
                [p.get("content", p.get("text", "")) for p in passages[: body.top_k]]
            )

            # Build enhanced context prompt with full session context
            if body.session_id:
                prompt = await self._answer.build_enhanced_context_prompt(
                    uow.session, body.session_id, body.query, passages_ctx, body.additional_context
                )
            else:
                # Use a simpler prompt when no session context is available
                prompt = await self._answer.build_prompt(body.query, passages[: body.top_k])

            # Generate response with enhanced prompt
            client = self._answer.model_registry.get_client(body.answer_model, body)

            start_time = time.time()

            if body.stream:

                async def _gen():
                    response_chunks = []
                    async for chunk in client.astream(
                        prompt=prompt, temperature=body.temperature, max_tokens=body.max_tokens
                    ):
                        response_chunks.append(chunk)
                        yield chunk

                    # Calculate processing time
                    processing_time = int((time.time() - start_time) * 1000)

                    # Save messages if session exists
                    if body.session_id:
                        full_response = "".join(response_chunks)
                        await self._answer.save_message(
                            uow.session,
                            body.session_id,
                            MessageRole.assistant,
                            full_response,
                            context_passages=passages[: body.top_k],
                            retrieval_query=body.query,
                            model_used=body.answer_model,
                            generation_params={
                                "temperature": body.temperature,
                                "max_tokens": body.max_tokens,
                                "model": body.answer_model,
                            },
                            processing_time_ms=processing_time,
                        )

                return StreamingResponse(_gen(), media_type="text/plain")

            # Non-streaming response
            text = await client.generate(
                prompt=prompt,
                temperature=body.temperature,
                max_tokens=body.max_tokens,
            )

            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)

            # Save messages if session exists
            if body.session_id:
                await self._answer.save_message(
                    uow.session,
                    body.session_id,
                    MessageRole.assistant,
                    text,
                    context_passages=passages[: body.top_k],
                    retrieval_query=body.query,
                    model_used=body.answer_model,
                    generation_params={
                        "temperature": body.temperature,
                        "max_tokens": body.max_tokens,
                        "model": body.answer_model,
                    },
                    processing_time_ms=processing_time,
                )

            return {
                "answer": text,
                "model": body.answer_model,
                "top_k": body.top_k,
                "mode": body.mode,
                "passages": passages[: body.top_k],
                "session_id": body.session_id,
                "processing_time_ms": processing_time,
            }
