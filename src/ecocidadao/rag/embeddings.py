from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, Callable, Protocol, Sequence

from ..config import get_settings

DEFAULT_MODEL_NAME = (
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)


class EmbeddingModel(Protocol):
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        ...

    def embed_query(self, text: str) -> list[float]:
        ...


class LocalEmbeddingModel:
    """Wrapper local para sentence-transformers, sem chamadas de nuvem."""

    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
        cache_dir: Path | str | None = None,
        batch_size: int = 32,
        normalize_embeddings: bool = True,
        model_factory: Callable[..., Any] | None = None,
    ) -> None:
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        self.device = device or settings.embedding_device
        self.cache_dir = Path(cache_dir or settings.hf_home)
        self.batch_size = batch_size
        self.normalize_embeddings = normalize_embeddings
        self._model_factory = model_factory
        self._model: Any | None = None

    def _build_model(self) -> Any:
        if self._model_factory is not None:
            return self._model_factory(
                self.model_name,
                device=self.device,
                cache_folder=str(self.cache_dir),
            )

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("HF_HOME", str(self.cache_dir))

        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(
            self.model_name,
            device=self.device,
            cache_folder=str(self.cache_dir),
        )

    @property
    def model(self) -> Any:
        if self._model is None:
            self._model = self._build_model()
        return self._model

    @property
    def dimension(self) -> int:
        dimension = self.model.get_sentence_embedding_dimension()
        if dimension is None:
            raise RuntimeError(
                "Nao foi possivel determinar a dimensao do modelo."
            )
        return int(dimension)

    def _encode(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []

        vectors = self.model.encode(
            list(texts),
            batch_size=self.batch_size,
            normalize_embeddings=self.normalize_embeddings,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return [
            [float(value) for value in vector]
            for vector in vectors
        ]

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return self._encode(texts)

    def embed_query(self, text: str) -> list[float]:
        vectors = self._encode([text])
        return vectors[0]

    async def aembed_documents(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        return await asyncio.to_thread(
            self.embed_documents,
            list(texts),
        )

    async def aembed_query(self, text: str) -> list[float]:
        return await asyncio.to_thread(self.embed_query, text)


def get_embedding_model() -> LocalEmbeddingModel:
    return LocalEmbeddingModel()
