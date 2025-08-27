from typing import Any, Dict

from fastapi.responses import StreamingResponse

from repositories.retrieval_repo import RetrievalRepo
from services.retrieval_service import RetrievalService


class AnswerService:
    def __init__(self, *, retrieval_svc: RetrievalService, model_registry):
        self.retrieval_svc = retrieval_svc
        self.model_registry = model_registry

    async def build_prompt(self, query: str, passages: list[dict]) -> str:
        ctx = "\n\n".join(f"- {p['text']}" for p in passages)
        return (
            "You are a helpful assistant.\n\n"
            f"Question:\n{query}\n\n"
            "Context (use it for grounding; quote minimally):\n"
            f"{ctx}\n\n"
            "Answer (có trích dẫn ngắn nếu cần):"
        )

    async def answer(self, body, repo: RetrievalRepo) -> Dict[str, Any]:
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
