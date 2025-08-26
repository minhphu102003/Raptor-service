from dataclasses import dataclass


@dataclass
class ModelRef:
    model: str
    factory: str | None


def parse_model_ref(s: str) -> ModelRef:
    parts = s.split("@", 1)
    return ModelRef(model=parts[0], factory=parts[1] if len(parts) == 2 else None)


@dataclass
class Creds:
    openai: str | None = None
    azure: dict | None = None
    cohere: str | None = None
    hf: str | None = None
    dashscope: str | None = None
    gemini: str | None = None
