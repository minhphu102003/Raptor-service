from enum import Enum


class SummarizeModel(str, Enum):
    GEMINI_FAST = "gemini-2.5-flash"
    DEEPSEEK_V3 = "DeepSeek-V3"
    QWEN3_235B = "Qwen3-235B-A22B"
