from typing import Any, List, Optional

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import ConfigDict, PrivateAttr

from .client import FPTLLMClient


def _to_openai_style(messages: List[BaseMessage]):
    out = []
    for m in messages:
        if isinstance(m, SystemMessage):
            out.append({"role": "system", "content": m.content})
        elif isinstance(m, HumanMessage):
            out.append({"role": "user", "content": m.content})
        else:  # AIMessage / others
            out.append({"role": "assistant", "content": m.content})
    return out


class FPTChatModel(BaseChatModel):
    """Adapter FPTLLMClient -> LangChain ChatModel."""

    # (không bắt buộc nhưng khuyến nghị) cho phép type lạ trong model nếu sau này thêm field
    model_config = ConfigDict(arbitrary_types_allowed=True)

    model_name: str = "DeepSeek-V3"
    temperature: Optional[float] = 0.0
    top_p: Optional[float] = 1.0
    max_tokens: Optional[int] = None

    _fpt: FPTLLMClient = PrivateAttr()

    def __init__(self, fpt_client: FPTLLMClient, **kwargs: Any):
        super().__init__(**kwargs)
        self._fpt = fpt_client

    @property
    def _llm_type(self) -> str:
        return "fpt-chat"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        payload = _to_openai_style(messages)
        resp = self._fpt.chat_completions(
            model=self._fpt.model or self.model_name,
            messages=payload,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            stream=False,
        )
        # Since stream=False, resp should be a Dict[str, Any]
        if not isinstance(resp, dict):
            raise ValueError("Expected dictionary response when stream=False")

        text = resp["choices"][0]["message"]["content"].strip()
        ai = AIMessage(content=text)
        return ChatResult(generations=[ChatGeneration(message=ai)])
