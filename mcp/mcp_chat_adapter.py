from typing import Any, List, Optional

from langchain_core.callbacks import AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import ConfigDict, PrivateAttr

from .mcp_client import MCPClient


def _to_openai_style(messages: List[BaseMessage]):
    """Convert LangChain messages to OpenAI-style format"""
    out = []
    for m in messages:
        if isinstance(m, SystemMessage):
            out.append({"role": "system", "content": m.content})
        elif isinstance(m, HumanMessage):
            out.append({"role": "user", "content": m.content})
        else:  # AIMessage / others
            out.append({"role": "assistant", "content": m.content})
    return out


class MCPChatModel(BaseChatModel):
    """Adapter MCP Client -> LangChain ChatModel."""

    # Allow arbitrary types in model
    model_config = ConfigDict(arbitrary_types_allowed=True)

    model_name: str = "mcp-default"
    temperature: Optional[float] = 0.0
    top_p: Optional[float] = 1.0
    max_tokens: Optional[int] = None
    mcp_endpoint: str = "default"

    _mcp_client: MCPClient = PrivateAttr()

    def __init__(self, mcp_client: MCPClient, **kwargs: Any):
        super().__init__(**kwargs)
        self._mcp_client = mcp_client

    @property
    def _llm_type(self) -> str:
        return "mcp-chat"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate response using MCP service"""
        payload = _to_openai_style(messages)

        # This would need to be async in a real implementation
        # For now, we'll simulate the response
        text = f"Simulated response from MCP model {self.model_name} for messages: {messages}"
        ai = AIMessage(content=text)
        return ChatResult(generations=[ChatGeneration(message=ai)])

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Async generate response using MCP service"""
        payload = _to_openai_style(messages)

        try:
            # Use the MCP client to get response
            response = await self._mcp_client.chat_completions(
                model=self.model_name,
                messages=payload,
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens,
                stream=False,
            )

            # Parse the response
            if isinstance(response, dict) and "choices" in response:
                content = response["choices"][0]["message"]["content"].strip()
                ai = AIMessage(content=content)
                return ChatResult(generations=[ChatGeneration(message=ai)])
            else:
                raise ValueError(f"Unexpected response format from MCP: {type(response)}")

        except Exception as e:
            raise Exception(f"Failed to generate response from MCP: {e}")
