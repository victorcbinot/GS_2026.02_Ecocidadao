from __future__ import annotations

from pydantic import SecretStr
from langchain_ollama import ChatOllama

from ..config import Settings, get_settings, is_local_ollama_url


class LLMConfigurationError(ValueError):
    pass


def _secret_text(value: SecretStr | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, SecretStr):
        return value.get_secret_value().strip()
    return str(value).strip()


def create_chat_model(
    settings: Settings | None = None,
    *,
    model: str | None = None,
    base_url: str | None = None,
    api_key: SecretStr | str | None = None,
    timeout_s: int | None = None,
) -> ChatOllama:
    settings = settings or get_settings()
    resolved_model = (settings.ollama_model if model is None else model).strip()
    resolved_base_url = (
        settings.ollama_base_url if base_url is None else base_url
    ).strip()
    resolved_api_key = _secret_text(
        settings.ollama_api_key if api_key is None else api_key
    )
    resolved_timeout = int(
        settings.llm_timeout_s if timeout_s is None else timeout_s
    )

    if not resolved_model:
        raise LLMConfigurationError(
            "OLLAMA_MODEL nao esta configurado no ambiente."
        )
    if not is_local_ollama_url(resolved_base_url) and not resolved_api_key:
        raise LLMConfigurationError(
            "OLLAMA_API_KEY nao esta configurada para o Ollama remoto."
        )

    client_kwargs: dict[str, object] = {
        "timeout": resolved_timeout,
    }
    if resolved_api_key:
        client_kwargs["headers"] = {
            "Authorization": f"Bearer {resolved_api_key}"
        }

    chat_kwargs: dict[str, object] = {
        "model": resolved_model,
        "base_url": resolved_base_url,
        "temperature": settings.llm_temperature,
        "num_predict": settings.llm_max_tokens,
        "validate_model_on_init": False,
        "client_kwargs": client_kwargs,
    }
    if (
        settings.llm_num_gpu is not None
        and is_local_ollama_url(resolved_base_url)
    ):
        chat_kwargs["num_gpu"] = settings.llm_num_gpu

    return ChatOllama(**chat_kwargs)


def create_judge_chat_model(settings: Settings | None = None) -> ChatOllama:
    settings = settings or get_settings()
    return create_chat_model(
        settings,
        model=settings.ragas_judge_model,
        base_url=settings.ragas_judge_base_url,
        api_key=settings.ragas_judge_api_key,
        timeout_s=settings.ragas_judge_timeout_s,
    )


__all__ = [
    "LLMConfigurationError",
    "create_chat_model",
    "create_judge_chat_model",
]
