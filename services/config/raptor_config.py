from dataclasses import dataclass
import os
from typing import Any, Dict, Optional


@dataclass
class RaptorConfig:
    """Configuration for RAPTOR tree building"""

    # Clustering parameters
    min_k: int = 2
    max_k: int = 50

    # LLM parameters
    max_tokens: int = 512
    rpm_limit: int = 3
    llm_concurrency: int = 3

    # Embedding throttling
    min_embed_interval: float = 20.0  # seconds between embeddings

    # Tree building parameters
    max_tree_levels: int = 10
    min_cluster_size: int = 2
    max_cluster_size: int = 100

    # Performance tuning
    enable_parallel_summarization: bool = True
    enable_embedding_cache: bool = True

    @classmethod
    def from_env(cls) -> "RaptorConfig":
        """Create RaptorConfig from environment variables"""
        return cls(
            min_k=int(os.getenv("RAPTOR_MIN_K", "2")),
            max_k=int(os.getenv("RAPTOR_MAX_K", "50")),
            max_tokens=int(os.getenv("RAPTOR_MAX_TOKENS", "512")),
            rpm_limit=int(os.getenv("RAPTOR_RPM_LIMIT", "3")),
            llm_concurrency=int(os.getenv("RAPTOR_LLM_CONCURRENCY", "3")),
            min_embed_interval=float(os.getenv("RAPTOR_MIN_EMBED_INTERVAL", "20.0")),
            max_tree_levels=int(os.getenv("RAPTOR_MAX_TREE_LEVELS", "10")),
            min_cluster_size=int(os.getenv("RAPTOR_MIN_CLUSTER_SIZE", "2")),
            max_cluster_size=int(os.getenv("RAPTOR_MAX_CLUSTER_SIZE", "100")),
            enable_parallel_summarization=os.getenv(
                "RAPTOR_ENABLE_PARALLEL_SUMMARIZATION", "true"
            ).lower()
            == "true",
            enable_embedding_cache=os.getenv("RAPTOR_ENABLE_EMBEDDING_CACHE", "true").lower()
            == "true",
        )

    def get_params_dict(self) -> Dict[str, Any]:
        """Get parameters as dictionary for backward compatibility"""
        return {
            "min_k": self.min_k,
            "max_k": self.max_k,
            "max_tokens": self.max_tokens,
            "rpm_limit": self.rpm_limit,
            "llm_concurrency": self.llm_concurrency,
        }
