from services.fpt_llm.client import FPTLLMClient
from services.fpt_llm.fpt_chat_adapter import FPTChatModel


def get_edge_decider_llm() -> FPTChatModel:
    """Trả về ChatModel dùng cho LLM_EDGE_PROMPT."""
    fpt = FPTLLMClient(model="DeepSeek-V3")  # dùng key/base_url từ env như bạn đã làm
    return FPTChatModel(
        fpt_client=fpt, model_name="DeepSeek-V3", temperature=0.0, top_p=1.0, max_tokens=8000
    )
