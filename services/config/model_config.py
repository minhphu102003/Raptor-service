from dataclasses import dataclass, field
from enum import Enum
import os
from typing import Any, Dict, Optional


class LLMProvider(str, Enum):
    """Supported LLM providers"""

    OPENAI = "openai"
    GEMINI = "gemini"
    FPT = "fpt"
    ANTHROPIC = "anthropic"


@dataclass
class ModelConfig:
    """Configuration for LLM models"""

    # Default models for each provider
    DEFAULT_MODELS: Dict[LLMProvider, str] = field(
        default_factory=lambda: {
            LLMProvider.OPENAI: "gpt-4o-mini",
            LLMProvider.GEMINI: "gemini-2.5-flash",
            LLMProvider.FPT: "DeepSeek-V3",
            LLMProvider.ANTHROPIC: "claude-3.5-haiku",
        }
    )

    # Model aliases mapping
    MODEL_ALIASES: Dict[str, str] = field(
        default_factory=lambda: {
            # DeepSeek aliases
            "deepseek-v3": "DeepSeek-V3",
            "deepseek": "DeepSeek-V3",
            # OpenAI aliases
            "gpt-4o-mini": "gpt-4o-mini",
            "gpt4o-mini": "gpt-4o-mini",
            "gpt-4.1": "gpt-4o",
            "gpt-4.1-mini": "gpt-4o-mini",
            # Gemini aliases
            "gemini-1.5-pro": "gemini-1.5-pro",
            "gemini-15-pro": "gemini-1.5-pro",
            "gemini-2.5-flash": "gemini-2.5-flash",
            "gemini-25-flash": "gemini-2.5-flash",
            "gemini25flash": "gemini-2.5-flash",
            "gemini2.5flash": "gemini-2.5-flash",
            # Anthropic aliases
            "claude-3.5-haiku": "claude-3.5-haiku",
            "claude35haiku": "claude-3.5-haiku",
            "claude-3-5-haiku": "claude-3.5-haiku",
            # Other aliases
            "Qwen3-235B-A22B": "Qwen3-235B-A22B",
        }
    )

    # Provider routing
    PROVIDER_ROUTING: Dict[str, LLMProvider] = field(
        default_factory=lambda: {
            # DeepSeek models
            "DeepSeek-V3": LLMProvider.FPT,
            "deepseek-v3": LLMProvider.FPT,
            "deepseek": LLMProvider.FPT,
            # OpenAI models
            "gpt-4o-mini": LLMProvider.OPENAI,
            "gpt4o-mini": LLMProvider.OPENAI,
            "gpt-4o": LLMProvider.OPENAI,
            "gpt-4.1": LLMProvider.OPENAI,
            "gpt-4.1-mini": LLMProvider.OPENAI,
            # Gemini models
            "gemini-1.5-pro": LLMProvider.GEMINI,
            "gemini-15-pro": LLMProvider.GEMINI,
            "gemini-2.5-flash": LLMProvider.GEMINI,
            "gemini-25-flash": LLMProvider.GEMINI,
            "gemini25flash": LLMProvider.GEMINI,
            "gemini2.5flash": LLMProvider.GEMINI,
            # Anthropic models
            "claude-3.5-haiku": LLMProvider.ANTHROPIC,
            "claude35haiku": LLMProvider.ANTHROPIC,
            "claude-3-5-haiku": LLMProvider.ANTHROPIC,
            # Other models
            "Qwen3-235B-A22B": LLMProvider.FPT,
        }
    )

    # Default generation parameters
    default_temperature: float = 0.7
    default_top_p: float = 1.0
    default_max_tokens: int = 8000

    # Summarization-specific parameters
    summarization_temperature: float = 0.2
    summarization_max_tokens: int = 8000

    # Model-specific context limits
    CONTEXT_LIMITS: Dict[str, int] = field(
        default_factory=lambda: {
            "gpt-4o-mini": 128000,
            "gpt-4o": 128000,
            "gpt-4.1": 128000,
            "gpt-4.1-mini": 128000,
            "gemini-1.5-pro": 2097152,
            "gemini-2.5-flash": 1048576,
            "DeepSeek-V3": 65536,
            "claude-3.5-haiku": 200000,
            "Qwen3-235B-A22B": 32768,
        }
    )

    @classmethod
    def from_env(cls) -> "ModelConfig":
        """Create ModelConfig from environment variables"""
        return cls(
            default_temperature=float(os.getenv("DEFAULT_TEMPERATURE", "0.7")),
            default_top_p=float(os.getenv("DEFAULT_TOP_P", "1.0")),
            default_max_tokens=int(os.getenv("DEFAULT_MAX_TOKENS", "8000")),
            summarization_temperature=float(os.getenv("SUMMARIZATION_TEMPERATURE", "0.2")),
            summarization_max_tokens=int(os.getenv("SUMMARIZATION_MAX_TOKENS", "8000")),
        )

    def normalize_model_name(self, name: str) -> str:
        """Normalize model name using aliases"""
        normalized = (name or "").strip().lower().replace(" ", "").replace("_", "-")
        return self.MODEL_ALIASES.get(normalized, name)

    def get_provider(self, model_name: str) -> LLMProvider:
        """Get provider for a given model"""
        normalized = self.normalize_model_name(model_name)
        return self.PROVIDER_ROUTING.get(normalized, LLMProvider.FPT)

    def get_context_limit(self, model_name: str) -> int:
        """Get context limit for a model"""
        normalized = self.normalize_model_name(model_name)
        return self.CONTEXT_LIMITS.get(normalized, 32768)

    def get_default_model(self, provider: LLMProvider) -> str:
        """Get default model for a provider"""
        return self.DEFAULT_MODELS.get(provider, "DeepSeek-V3")
