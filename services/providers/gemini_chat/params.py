from dataclasses import dataclass


@dataclass(frozen=True)
class GenerateParams:
    max_tokens: int = 512
    temperature: float = 0.2
    mime: str = "text/plain"
    candidates: int = 1
    disable_afc: bool = True
    thinking_budget: int = 64
