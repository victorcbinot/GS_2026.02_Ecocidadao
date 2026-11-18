from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def is_local_ollama_url(base_url: str) -> bool:
    host = (urlparse(base_url).hostname or "").casefold()
    return host in {
        "localhost",
        "127.0.0.1",
        "::1",
        "0.0.0.0",
        "host.docker.internal",
    }


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "EcoCidadão"
    app_env: str = "dev"
    log_level: str = "INFO"

    ollama_api_key: SecretStr | None = None
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = ""
    llm_temperature: float = 0.1
    llm_max_tokens: int = 1024
    llm_timeout_s: int = 60

    ragas_judge_api_key: SecretStr | None = None
    ragas_judge_base_url: str = "http://127.0.0.1:11434"
    ragas_judge_model: str = "qwen2.5:7b"
    ragas_judge_timeout_s: int = 300

    embedding_model: str = (
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    embedding_device: str = "cpu"
    hf_home: Path = PROJECT_ROOT / ".cache" / "huggingface"

    base_docs_dir: Path = PROJECT_ROOT / "base_documental"
    chroma_dir: Path = PROJECT_ROOT / "data" / "chroma"
    ecopontos_data_path: Path = PROJECT_ROOT / "data" / "ecopontos.json"
    evaluation_dataset_path: Path = (
        PROJECT_ROOT / "src" / "ecocidadao" / "evaluation" / "dataset.json"
    )
    ragas_output_path: Path = PROJECT_ROOT / "avaliacao_ragas.json"
    chunking_experiment_path: Path = (
        PROJECT_ROOT / "data" / "experiments" / "chunking_comparison.json"
    )

    collection_name: str = "ecocidadao_markdown"
    retrieval_top_k: int = Field(default=6, ge=1)
    retrieval_fetch_k: int = Field(default=20, ge=1)
    retrieval_score_threshold: float = Field(default=0.35, ge=0.0, le=1.0)
    max_context_chars: int = Field(default=8000, ge=1)
    max_input_chars: int = Field(default=2000, ge=1)
    max_tool_calls: int = Field(default=6, ge=1, le=6)

    gradio_server_name: str = "127.0.0.1"
    gradio_server_port: int = Field(default=7860, ge=1, le=65535)

    @property
    def has_ollama_credentials(self) -> bool:
        return bool(
            self.ollama_api_key
            and self.ollama_api_key.get_secret_value().strip()
        )

    @property
    def has_ragas_judge_credentials(self) -> bool:
        return bool(
            self.ragas_judge_api_key
            and self.ragas_judge_api_key.get_secret_value().strip()
        )

    @property
    def uses_local_ollama(self) -> bool:
        """Indica se o Ollama principal roda localmente."""
        return is_local_ollama_url(self.ollama_base_url)

    @property
    def uses_local_ragas_judge(self) -> bool:
        """Indica se o Ollama juiz do RAGAS roda localmente."""
        return is_local_ollama_url(self.ragas_judge_base_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()
