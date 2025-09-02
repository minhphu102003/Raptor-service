from constants.enum import SummarizeModel
from interfaces_adaptor.http.dtos import IngestMarkdownPayload
from services.clustering.summarizer import make_llm


def get_llm_from_payload(payload: IngestMarkdownPayload):
    """
    Trích xuất summary_llm từ payload, nếu không có thì mặc định GEMINI_FAST.
    Trả về instance từ make_llm().
    """
    model_name = payload.summary_llm or SummarizeModel.GEMINI_FAST.value
    try:
        model_enum = SummarizeModel(model_name)
    except ValueError:
        raise ValueError(
            f"Invalid summary_llm: {model_name}. Must be one of {[m.value for m in SummarizeModel]}"
        )

    return make_llm(model_enum.value)
