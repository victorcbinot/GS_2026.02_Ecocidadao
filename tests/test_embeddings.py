from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from ecocidadao.rag.embeddings import (
        DEFAULT_MODEL_NAME,
        LocalEmbeddingModel,
    )

    EMBEDDINGS_AVAILABLE = True
except ImportError as error:
    EMBEDDINGS_AVAILABLE = False
    EMBEDDINGS_IMPORT_ERROR = error


class FakeSentenceTransformer:
    def __init__(
        self,
        model_name: str,
        device: str | None = None,
        cache_folder: str | None = None,
    ) -> None:
        self.model_name = model_name
        self.device = device
        self.cache_folder = cache_folder
        self.calls: list[list[str]] = []

    def encode(
        self,
        texts: list[str],
        batch_size: int = 32,
        normalize_embeddings: bool = True,
        convert_to_numpy: bool = True,
        show_progress_bar: bool = False,
    ) -> list[list[float]]:
        self.calls.append(list(texts))
        vectors = []
        for text in texts:
            vectors.append(
                [
                    float(len(text)),
                    float(text.lower().count("pilha")),
                    float(text.lower().count("medicamento")),
                ]
            )
        return vectors

    def get_sentence_embedding_dimension(self) -> int:
        return 3


@unittest.skipUnless(
    EMBEDDINGS_AVAILABLE,
    "Dependencias de embeddings nao instaladas.",
)
class LocalEmbeddingModelTests(unittest.TestCase):
    def test_embeddings_and_query_use_injected_local_model(self) -> None:
        fake = FakeSentenceTransformer("modelo-local")
        model = LocalEmbeddingModel(
            model_name="modelo-local",
            device="cpu",
            batch_size=2,
            model_factory=lambda *args, **kwargs: fake,
        )

        document_vectors = model.embed_documents(["pilhas", "medicamentos"])
        query_vector = model.embed_query("pilhas")

        self.assertEqual(document_vectors[0][:2], [6.0, 1.0])
        self.assertEqual(document_vectors[1][:2], [12.0, 0.0])
        self.assertEqual(query_vector[:2], [6.0, 1.0])
        self.assertEqual(model.dimension, 3)
        self.assertEqual(len(fake.calls), 2)

    def test_empty_document_batch_returns_empty_list(self) -> None:
        model = LocalEmbeddingModel(
            model_factory=lambda *args, **kwargs: FakeSentenceTransformer(
                "modelo-local"
            )
        )

        self.assertEqual(model.embed_documents([]), [])

    def test_default_model_is_multilingual_minilm(self) -> None:
        self.assertEqual(
            DEFAULT_MODEL_NAME,
            (
                "sentence-transformers/"
                "paraphrase-multilingual-MiniLM-L12-v2"
            ),
        )


if __name__ == "__main__":
    unittest.main()
