from dataclasses import dataclass
from typing import Any, Dict, List, Optional

DEFAULT_BASE_URL = "https://mkp-api.fptcloud.com"


@dataclass
class ChatMessage:
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str


@dataclass
class ChatCompletionChunk:
    id: Optional[str]
    created: Optional[int]
    model: Optional[str]
    delta: str
    raw: Dict[str, Any]
