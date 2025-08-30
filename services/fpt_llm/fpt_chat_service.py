from typing import Optional

from services.config import LLMProvider, ModelConfig, get_service_config
from services.exceptions import ConfigurationError, ModelNotSupportedError
from services.fpt_llm.client import FPTLLMClient
from services.fpt_llm.fpt_chat_adapter import FPTChatModel


def get_edge_decider_llm(config: Optional[ModelConfig] = None) -> FPTChatModel:
    """Return ChatModel for LLM_EDGE_PROMPT with configuration support."""
    if config is None:
        config = get_service_config().model_config

    # Get default FPT model from configuration
    default_model = config.get_default_model(LLMProvider.FPT)

    try:
        # Validate model is supported by FPT provider
        if config.get_provider(default_model) != LLMProvider.FPT:
            raise ModelNotSupportedError(default_model, ["FPT provider models"])

        fpt = FPTLLMClient(model=default_model)
        return FPTChatModel(
            fpt_client=fpt,
            model_name=default_model,
            temperature=config.default_temperature,
            top_p=config.default_top_p,
            max_tokens=config.default_max_tokens,
        )

    except Exception as e:
        if isinstance(e, ModelNotSupportedError):
            raise
        raise ConfigurationError(
            f"Failed to create edge decider LLM with model {default_model}",
            error_code="EDGE_DECIDER_LLM_CREATION_FAILED",
            context={"model": default_model},
            cause=e,
        )


def create_fpt_chat_model(
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    max_tokens: Optional[int] = None,
    config: Optional[ModelConfig] = None,
) -> FPTChatModel:
    """Create FPT chat model with configurable parameters."""
    if config is None:
        config = get_service_config().model_config

    # Use defaults from config if not provided
    model_name = model_name or config.get_default_model(LLMProvider.FPT)
    temperature = temperature if temperature is not None else config.default_temperature
    top_p = top_p if top_p is not None else config.default_top_p
    max_tokens = max_tokens or config.default_max_tokens

    try:
        # Validate model is supported by FPT provider
        if config.get_provider(model_name) != LLMProvider.FPT:
            raise ModelNotSupportedError(model_name, ["FPT provider models"])

        fpt = FPTLLMClient(model=model_name)
        return FPTChatModel(
            fpt_client=fpt,
            model_name=model_name,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )

    except Exception as e:
        if isinstance(e, ModelNotSupportedError):
            raise
        raise ConfigurationError(
            f"Failed to create FPT chat model {model_name}",
            error_code="FPT_CHAT_MODEL_CREATION_FAILED",
            context={
                "model_name": model_name,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
            },
            cause=e,
        )
