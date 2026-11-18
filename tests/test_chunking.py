from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ecocidadao.ingestion import chunk_documents, load_documents

DOCS_DIR = PROJECT_ROOT / "base_documental"


def _normalize(text: str) -> str:
    return " ".join(text.split())


class ChunkingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.documents = load_documents(DOCS_DIR)
        cls.by_id = {document.doc_id: document for document in cls.documents}
        cls.fixed_chunks = chunk_documents(cls.documents, "fixo")
        cls.markdown_chunks = chunk_documents(cls.documents, "markdown")

    def test_both_strategies_generate_chunks_for_every_document(self) -> None:
        for chunks in (self.fixed_chunks, self.markdown_chunks):
            self.assertGreater(len(chunks), 0)
            chunk_doc_ids = {chunk.doc_id for chunk in chunks}
            self.assertEqual(
                chunk_doc_ids,
                {document.doc_id for document in self.documents},
            )

    def test_chunk_ids_are_unique_and_deterministic(self) -> None:
        for strategy, first_run in (
            ("fixo", self.fixed_chunks),
            ("markdown", self.markdown_chunks),
        ):
            second_run = chunk_documents(self.documents, strategy)
            first_signature = [
                (
                    chunk.chunk_id,
                    chunk.text,
                    json.dumps(chunk.metadata, sort_keys=True),
                )
                for chunk in first_run
            ]
            second_signature = [
                (
                    chunk.chunk_id,
                    chunk.text,
                    json.dumps(chunk.metadata, sort_keys=True),
                )
                for chunk in second_run
            ]
            self.assertEqual(first_signature, second_signature)
            chunk_ids = [chunk.chunk_id for chunk in first_run]
            self.assertEqual(len(chunk_ids), len(set(chunk_ids)))
            for chunk in first_run:
                self.assertTrue(
                    chunk.chunk_id.startswith(
                        f"{chunk.doc_id}::{strategy}::"
                    )
                )

    def test_chunk_size_limit_is_respected(self) -> None:
        for chunks in (self.fixed_chunks, self.markdown_chunks):
            for chunk in chunks:
                self.assertLessEqual(len(chunk.text), 800)
                self.assertGreater(len(chunk.text.strip()), 0)

    def test_required_metadata_is_inherited_by_chunks(self) -> None:
        for chunks in (self.fixed_chunks, self.markdown_chunks):
            for chunk in chunks:
                metadata = chunk.metadata
                for key in (
                    "titulo",
                    "data_publicacao",
                    "tema",
                    "doc_id",
                    "source_file",
                    "chunk_id",
                    "chunk_strategy",
                    "chunk_content_hash",
                    "document_content_hash",
                ):
                    self.assertIn(key, metadata)
                self.assertEqual(metadata["doc_id"], chunk.doc_id)
                self.assertEqual(metadata["chunk_id"], chunk.chunk_id)
                self.assertEqual(metadata["titulo"], self.by_id[chunk.doc_id].titulo)

    def test_markdown_strategy_preserves_heading_hierarchy(self) -> None:
        sectioned_chunks = [
            chunk
            for chunk in self.markdown_chunks
            if chunk.metadata.get("section_h2")
        ]
        self.assertGreater(len(sectioned_chunks), 0)

        hidden_detail_chunk = next(
            chunk
            for chunk in self.markdown_chunks
            if "Farmácia Municipal EcoSaúde" in _normalize(chunk.text)
        )
        metadata = hidden_detail_chunk.metadata
        self.assertEqual(
            metadata["section_h1"],
            "Regulamento de Descarte de Resíduos de EcoCidade",
        )
        self.assertEqual(
            metadata["section_h2"],
            "6. Descarte de medicamentos e resíduos de saúde",
        )
        self.assertEqual(metadata["section_level"], 2)
        self.assertEqual(
            metadata["section_path"],
            [
                "Regulamento de Descarte de Resíduos de EcoCidade",
                "6. Descarte de medicamentos e resíduos de saúde",
            ],
        )
        self.assertIn(
            "6. Descarte de medicamentos e resíduos de saúde",
            metadata["section_path_text"],
        )

    def test_chunk_text_preserves_document_content(self) -> None:
        for document in self.documents:
            normalized_document = _normalize(document.content)
            for strategy in ("fixo", "markdown"):
                chunks = chunk_documents([document], strategy)
                for chunk in chunks:
                    self.assertIn(
                        _normalize(chunk.text),
                        normalized_document,
                    )

    def test_key_facts_are_present_after_chunking(self) -> None:
        key_facts = (
            "Farmácia Municipal EcoSaúde",
            "Rua das Palmeiras, 77",
            "15 de março de 2026",
            "1º de junho de 2026",
            "deixa de aceitar pilhas e baterias",
        )
        for chunks in (self.fixed_chunks, self.markdown_chunks):
            joined_text = _normalize("\n".join(chunk.text for chunk in chunks))
            for fact in key_facts:
                self.assertIn(_normalize(fact), joined_text)

    def test_chunking_does_not_modify_source_documents(self) -> None:
        before = {
            document.path: document.path.read_bytes()
            for document in self.documents
        }
        chunk_documents(self.documents, "fixo")
        chunk_documents(self.documents, "markdown")
        after = {
            document.path: document.path.read_bytes()
            for document in self.documents
        }
        self.assertEqual(before, after)

    def test_invalid_strategy_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            chunk_documents(self.documents, "invalida")


if __name__ == "__main__":
    unittest.main()
