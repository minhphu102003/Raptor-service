from dataclasses import dataclass
import os
from typing import Optional

from .embedding_config import EmbeddingConfig
from .model_config import ModelConfig
from .raptor_config import RaptorConfig


@dataclass
class ServiceConfig:
    """Main configuration container for all services"""

    model_config: ModelConfig
    embedding_config: EmbeddingConfig
    raptor_config: RaptorConfig

    # Global service settings
    debug_mode: bool = False
    log_level: str = "INFO"
    enable_metrics: bool = True

    @classmethod
    def from_env(cls) -> "ServiceConfig":
        """Create ServiceConfig from environment variables"""
        return cls(
            model_config=ModelConfig.from_env(),
            embedding_config=EmbeddingConfig.from_env(),
            raptor_config=RaptorConfig.from_env(),
            debug_mode=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            enable_metrics=os.getenv("ENABLE_METRICS", "true").lower() == "true",
        )


# Global service configuration instance
_service_config: Optional[ServiceConfig] = None


def get_service_config() -> ServiceConfig:
    """Get global service configuration instance"""
    global _service_config
    if _service_config is None:
        _service_config = ServiceConfig.from_env()
    return _service_config


def set_service_config(config: ServiceConfig) -> None:
    """Set global service configuration (mainly for testing)"""
    global _service_config
    _service_config = config
