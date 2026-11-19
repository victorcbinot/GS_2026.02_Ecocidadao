from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from ecocidadao.config import Settings
    from ecocidadao.rag import (
        LLMConfigurationError,
        create_chat_model,
    )

    RAG_LLM_AVAILABLE = True
except ImportError as error:
    RAG_LLM_AVAILABLE = False
    RAG_LLM_IMPORT_ERROR = error


@unittest.skipUnless(
    RAG_LLM_AVAILABLE,
    "Dependencias do modelo Ollama nao instaladas.",
)
class ChatModelConfigurationTests(unittest.TestCase):
    def test_chat_model_uses_project_settings_without_hardcoded_key(self) -> None:
        settings = Settings(
            _env_file=None,
            ollama_api_key="test-key",
            ollama_base_url="https://ollama.example",
            ollama_model="test-model",
            llm_temperature=0.0,
            llm_max_tokens=321,
            llm_timeout_s=15,
        )

        llm = create_chat_model(settings)

        self.assertEqual(llm.model, "test-model")
        self.assertEqual(llm.base_url, "https://ollama.example")
        self.assertEqual(llm.temperature, 0.0)
        self.assertEqual(llm.num_predict, 321)
        self.assertEqual(
            llm.client_kwargs["headers"]["Authorization"],
            "Bearer test-key",
        )
        self.assertEqual(llm.client_kwargs["timeout"], 15)

    def test_missing_api_key_raises_for_remote_ollama(self) -> None:
        settings = Settings(
            _env_file=None,
            ollama_api_key=None,
            ollama_base_url="https://ollama.example",
            ollama_model="test-model",
        )

        with self.assertRaises(LLMConfigurationError):
            create_chat_model(settings)

    def test_local_ollama_does_not_require_api_key(self) -> None:
        settings = Settings(
            _env_file=None,
            ollama_api_key=None,
            ollama_base_url="http://127.0.0.1:11434",
            ollama_model="test-model",
        )

        llm = create_chat_model(settings)

        self.assertEqual(llm.model, "test-model")
        self.assertNotIn("headers", llm.client_kwargs)

    def test_local_ollama_can_limit_gpu_layers(self) -> None:
        settings = Settings(
            _env_file=None,
            ollama_api_key=None,
            ollama_base_url="http://127.0.0.1:11434",
            ollama_model="test-model",
            llm_num_gpu=28,
        )

        llm = create_chat_model(settings)

        self.assertEqual(llm.num_gpu, 28)

    def test_remote_ollama_ignores_gpu_layer_limit(self) -> None:
        settings = Settings(
            _env_file=None,
            ollama_api_key="test-key",
            ollama_base_url="https://ollama.example",
            ollama_model="test-model",
            llm_num_gpu=28,
        )

        llm = create_chat_model(settings)

        self.assertIsNone(llm.num_gpu)

    def test_missing_model_raises_configuration_error(self) -> None:
        settings = Settings(
            _env_file=None,
            ollama_api_key="test-key",
            ollama_base_url="https://ollama.example",
            ollama_model="",
        )

        with self.assertRaises(LLMConfigurationError):
            create_chat_model(settings)


if __name__ == "__main__":
    unittest.main()
