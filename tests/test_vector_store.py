from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from ecocidadao.ingestion import Chunk
    from ecocidadao.rag import (
        COLLECTION_FIXO,
        COLLECTION_MARKDOWN,
        ChromaVectorStore,
        CollectionNotFoundError,
        create_index,
        load_collection,
    )

    VECTOR_STORE_AVAILABLE = True
except ImportError as error:
    VECTOR_STORE_AVAILABLE = False
    VECTOR_STORE_IMPORT_ERROR = error


class FakeEmbeddingModel:
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)

    @staticmethod
    def _vector(text: str) -> list[float]:
        lower = text.lower()
        return [
            0.01 + float("pilha" in lower),
            0.01 + float("medicamento" in lower),
            0.01 + float("horario" in lower),
        ]


def _make_chunk(
    chunk_id: str,
    text: str,
    doc_id: str = "regulamento_descarte",
    index: int = 0,
) -> Chunk:
    metadata = {
        "titulo": "Regulamento de Descarte",
        "data_publicacao": "2026-01-20",
        "tema": "descarte",
        "doc_id": doc_id,
        "source_file": "regulamento_descarte.md",
        "document_content_hash": "doc-hash",
        "chunk_id": chunk_id,
        "chunk_index": index,
        "chunk_strategy": "fixo",
        "chunk_size_limit": 800,
        "chunk_overlap": 150,
        "char_count": len(text),
        "word_count": len(text.split()),
        "chunk_content_hash": f"hash-{chunk_id}",
        "section_h1": "Regulamento",
        "section_h2": "Descarte",
        "section_h3": None,
        "section_path": ["Regulamento", "Descarte"],
        "section_path_text": "Regulamento > Descarte",
        "section_level": 2,
    }
    return Chunk(
        chunk_id=chunk_id,
        doc_id=doc_id,
        text=text,
        metadata=metadata,
        chunk_index=index,
    )


@unittest.skipUnless(
    VECTOR_STORE_AVAILABLE,
    "chromadb ou dependencias do vector store nao instaladas.",
)
class ChromaVectorStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(
            tempfile.mkdtemp(prefix="ecocidadao-chroma-test-")
        )
        self.embedding_model = FakeEmbeddingModel()
        self.pilhas = _make_chunk(
            "regulamento_descarte::fixo::0000",
            "O descarte de pilhas e baterias deve ser feito no Ecoponto.",
        )
        self.medicamentos = _make_chunk(
            "regulamento_descarte::fixo::0001",
            "Medicamentos vencidos devem ir a Farmacia Municipal.",
            index=1,
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_index_and_query_returns_content_and_metadata(self) -> None:
        store = ChromaVectorStore(
            collection_name=COLLECTION_FIXO,
            chroma_dir=self.temp_dir,
            embedding_model=self.embedding_model,
        )

        result = store.create_or_update([self.pilhas, self.medicamentos])
        retrieved = store.query("Onde descarto pilhas?", top_k=1)

        self.assertEqual(result.indexed, 2)
        self.assertEqual(result.total, 2)
        self.assertEqual(len(retrieved), 1)
        self.assertEqual(retrieved[0].chunk_id, self.pilhas.chunk_id)
        self.assertEqual(retrieved[0].text, self.pilhas.text)
        self.assertEqual(retrieved[0].metadata, self.pilhas.metadata)
        self.assertAlmostEqual(retrieved[0].distance, 0.0, places=5)
        self.assertAlmostEqual(retrieved[0].similarity, 1.0, places=5)

    def test_repeated_indexing_does_not_duplicate_documents(self) -> None:
        store = ChromaVectorStore(
            collection_name=COLLECTION_FIXO,
            chroma_dir=self.temp_dir,
            embedding_model=self.embedding_model,
        )

        store.create_or_update([self.pilhas, self.medicamentos])
        store.create_or_update([self.pilhas, self.medicamentos])

        self.assertEqual(store.count(), 2)

        updated = _make_chunk(
            self.pilhas.chunk_id,
            "O descarte de pilhas recarregaveis segue a mesma regra.",
        )
        store.create_or_update([updated, self.medicamentos])

        self.assertEqual(store.count(), 2)
        self.assertEqual(store.get_by_ids([self.pilhas.chunk_id])[0].text, updated.text)

    def test_stale_chunks_are_removed_when_index_is_updated(self) -> None:
        store = ChromaVectorStore(
            collection_name=COLLECTION_FIXO,
            chroma_dir=self.temp_dir,
            embedding_model=self.embedding_model,
        )

        store.create_or_update([self.pilhas, self.medicamentos])
        result = store.create_or_update([self.pilhas])

        self.assertEqual(result.deleted, 1)
        self.assertEqual(store.count(), 1)
        self.assertEqual(store.get_by_ids([self.medicamentos.chunk_id]), [])

    def test_collection_persists_and_can_be_loaded_from_disk(self) -> None:
        store = ChromaVectorStore(
            collection_name=COLLECTION_FIXO,
            chroma_dir=self.temp_dir,
            embedding_model=self.embedding_model,
        )
        store.create_or_update([self.pilhas, self.medicamentos])

        loaded = load_collection(
            collection_name=COLLECTION_FIXO,
            chroma_dir=self.temp_dir,
            embedding_model=self.embedding_model,
        )
        retrieved = loaded.query("pilhas", top_k=1)

        self.assertEqual(loaded.count(), 2)
        self.assertIn(COLLECTION_FIXO, loaded.list_collections())
        self.assertEqual(retrieved[0].chunk_id, self.pilhas.chunk_id)

    def test_two_collections_are_independent(self) -> None:
        fixed_store = ChromaVectorStore(
            collection_name=COLLECTION_FIXO,
            chroma_dir=self.temp_dir,
            embedding_model=self.embedding_model,
        )
        markdown_store = ChromaVectorStore(
            collection_name=COLLECTION_MARKDOWN,
            chroma_dir=self.temp_dir,
            embedding_model=self.embedding_model,
        )

        fixed_store.create_or_update(
            [_make_chunk("shared", "pilhas e baterias")]
        )
        markdown_store.create_or_update(
            [_make_chunk("shared", "medicamentos vencidos")]
        )

        fixed_result = fixed_store.query("pilhas", top_k=1)
        markdown_result = markdown_store.query("medicamentos", top_k=1)

        self.assertEqual(fixed_store.count(), 1)
        self.assertEqual(markdown_store.count(), 1)
        self.assertEqual(fixed_result[0].text, "pilhas e baterias")
        self.assertEqual(markdown_result[0].text, "medicamentos vencidos")

    def test_missing_collection_raises_clear_error(self) -> None:
        with self.assertRaises(CollectionNotFoundError):
            load_collection(
                collection_name=COLLECTION_MARKDOWN,
                chroma_dir=self.temp_dir,
                embedding_model=self.embedding_model,
            )

    def test_create_index_helper_and_recreate(self) -> None:
        first_result = create_index(
            strategy="fixo",
            chunks=[self.pilhas, self.medicamentos],
            chroma_dir=self.temp_dir,
            embedding_model=self.embedding_model,
        )
        second_result = create_index(
            strategy="fixo",
            chunks=[self.pilhas],
            chroma_dir=self.temp_dir,
            embedding_model=self.embedding_model,
            replace_existing=True,
        )

        self.assertEqual(first_result.total, 2)
        self.assertEqual(second_result.total, 1)
        self.assertEqual(second_result.deleted, 0)

    def test_invalid_query_and_strategy_are_rejected(self) -> None:
        store = ChromaVectorStore(
            collection_name=COLLECTION_FIXO,
            chroma_dir=self.temp_dir,
            embedding_model=self.embedding_model,
        )
        store.create_or_update([self.pilhas])

        with self.assertRaises(ValueError):
            store.query("   ")
        with self.assertRaises(ValueError):
            store.query("pilhas", top_k=0)
        with self.assertRaises(ValueError):
            create_index(
                strategy="invalida",
                chunks=[self.pilhas],
                chroma_dir=self.temp_dir,
                embedding_model=self.embedding_model,
            )


if __name__ == "__main__":
    unittest.main()
