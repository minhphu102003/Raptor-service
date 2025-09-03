import json
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession


class PromptService:
    def __init__(self):
        pass

    async def build_enhanced_context_prompt(
        self,
        session_context: Dict[str, Any],
        current_query: str,
        passages_ctx: str,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        system_prompt = session_context.get("system_prompt") or "You are a helpful assistant."

        conversation_history = ""
        recent_messages = session_context.get("recent_messages", [])
        if recent_messages:
            formatted_messages = [f"{msg['role']}: {msg['content']}" for msg in recent_messages]
            conversation_history = "\n".join(formatted_messages)

        prompt_parts = [system_prompt]

        if conversation_history:
            prompt_parts.extend(["\nConversation History:", conversation_history])

        if additional_context:
            prompt_parts.extend(
                [
                    "\nAdditional Context:",
                    json.dumps(additional_context, indent=2, ensure_ascii=False),
                ]
            )

        prompt_parts.extend(
            [
                f"\nCurrent Question:\n{current_query}",
                f"\nRetrieved Context (use for grounding; quote minimally):\n{passages_ctx}",
                "\nAnswer (provide a helpful response based on the context and conversation history):",
            ]
        )

        return "\n".join(prompt_parts)

    async def build_prompt(self, query: str, passages: list[dict]) -> str:
        ctx = "\n\n".join(f"- {p.get('content', p.get('text', ''))}" for p in passages)
        return (
            "You are a helpful assistant.\n\n"
            f"Question:\n{query}\n\n"
            "Context (use it for grounding; quote minimally):\n"
            f"{ctx}\n\n"
            "Answer (có trích dẫn ngắn nếu cần):"
        )
