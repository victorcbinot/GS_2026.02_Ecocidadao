from __future__ import annotations

from langchain_ollama import ChatOllama

from ..config import Settings, get_settings


class LLMConfigurationError(ValueError):
    pass


def create_chat_model(settings: Settings | None = None) -> ChatOllama:
    settings = settings or get_settings()
    model = settings.ollama_model.strip()

    if not model:
        raise LLMConfigurationError(
            "OLLAMA_MODEL nao esta configurado no ambiente."
        )
    if not settings.has_ollama_credentials:
        raise LLMConfigurationError(
            "OLLAMA_API_KEY nao esta configurada no ambiente."
        )

    api_key = settings.ollama_api_key.get_secret_value().strip()
    return ChatOllama(
        model=model,
        base_url=settings.ollama_base_url,
        temperature=settings.llm_temperature,
        num_predict=settings.llm_max_tokens,
        validate_model_on_init=False,
        client_kwargs={
            "timeout": settings.llm_timeout_s,
            "headers": {"Authorization": f"Bearer {api_key}"},
        },
    )
