from dataclasses import dataclass, field
import os
from typing import Any, Dict, Optional


@dataclass
class EmbeddingConfig:
    """Configuration for embedding services"""

    # Default embedding settings
    default_model: str = "voyage-context-3"
    default_dimension: int = 1024
    batch_size: int = 100
    max_retries: int = 3
    retry_delay: float = 1.0

    # Supported models and their dimensions
    SUPPORTED_MODELS: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        if not self.SUPPORTED_MODELS:
            self.SUPPORTED_MODELS = {
                "voyage-context-3": 1024,
                "voyage-3": 1024,
                "text-embedding-3-large": 3072,
                "text-embedding-3-small": 1536,
                "text-embedding-ada-002": 1536,
            }

    @classmethod
    def from_env(cls) -> "EmbeddingConfig":
        """Create EmbeddingConfig from environment variables"""
        return cls(
            default_model=os.getenv("EMBEDDING_MODEL", "voyage-context-3"),
            default_dimension=int(os.getenv("EMBEDDING_DIMENSION", "1024")),
            batch_size=int(os.getenv("EMBEDDING_BATCH_SIZE", "100")),
            max_retries=int(os.getenv("EMBEDDING_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("EMBEDDING_RETRY_DELAY", "1.0")),
        )

    def get_dimension(self, model: str) -> int:
        """Get dimension for a specific model"""
        return self.SUPPORTED_MODELS.get(model, self.default_dimension)

    def is_supported_model(self, model: str) -> bool:
        """Check if model is supported"""
        return model in self.SUPPORTED_MODELS
