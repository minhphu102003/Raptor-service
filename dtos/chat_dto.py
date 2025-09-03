from typing import Annotated, Any, Dict, List, Literal, Optional

from fastapi import Query
from pydantic import BaseModel


# Request/Response Models
class CreateSessionRequest(BaseModel):
    dataset_id: str
    title: str = "New Chat"
    user_id: Optional[str] = None
    assistant_id: Optional[str] = None
    assistant_config: Optional[dict] = None


class ChatMessageRequest(BaseModel):
    query: str
    dataset_id: str
    session_id: Optional[str] = None

    # Retrieval parameters
    top_k: int = 5
    expand_k: int = 5
    mode: Literal["tree", "chunk"] = "tree"

    # Answer generation parameters
    answer_model: Literal["DeepSeek-V3", "GPT-4o-mini", "Gemini-2.5-Flash", "Claude-3.5-Haiku"] = (
        "DeepSeek-V3"
    )
    temperature: float = 0.7
    max_tokens: int = 4000
    stream: bool = False


class EnhancedChatMessageRequest(ChatMessageRequest):
    """Enhanced chat message request with additional context options"""

    use_enhanced_context: bool = True
    max_context_messages: int = 6
    additional_context: Optional[Dict[str, Any]] = None


class UpdateSessionRequest(BaseModel):
    title: Optional[str] = None
    assistant_config: Optional[dict] = None
