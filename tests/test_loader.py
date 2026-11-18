from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ecocidadao.ingestion import (
    DocumentValidationError,
    load_document,
    load_documents,
    validate_expected_documents,
)

DOCS_DIR = PROJECT_ROOT / "base_documental"


def _normalize(text: str) -> str:
    return " ".join(text.split())


def _write_document(directory: Path, name: str, content: str) -> Path:
    path = directory / name
    path.write_text(content, encoding="utf-8")
    return path


class DocumentLoaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.documents = load_documents(DOCS_DIR)
        cls.by_id = {document.doc_id: document for document in cls.documents}

    def test_loads_the_three_required_documents(self) -> None:
        filenames = {document.path.name for document in self.documents}
        self.assertEqual(
            filenames,
            {
                "regulamento_descarte.md",
                "lista_ecopontos.md",
                "comunicado_interdicao.md",
            },
        )
        self.assertEqual(len(self.documents), 3)

    def test_required_metadata_is_present_and_valid(self) -> None:
        for document in self.documents:
            self.assertIsInstance(document.titulo, str)
            self.assertTrue(document.titulo.strip())
            self.assertIsInstance(document.tema, str)
            self.assertTrue(document.tema.strip())
            self.assertIsInstance(document.data_publicacao, str)
            date.fromisoformat(document.data_publicacao)
            self.assertEqual(
                document.metadata["titulo"],
                document.titulo,
            )
            self.assertEqual(
                document.metadata["data_publicacao"],
                document.data_publicacao,
            )
            self.assertEqual(document.metadata["tema"], document.tema)

    def test_additional_metadata_is_preserved(self) -> None:
        for document in self.documents:
            for key in ("municipio", "orgao", "versao"):
                self.assertIn(key, document.metadata)
                self.assertTrue(str(document.metadata[key]).strip())
            self.assertEqual(document.metadata["municipio"], "EcoCidade")

    def test_original_content_and_hash_are_preserved(self) -> None:
        for document in self.documents:
            original = document.path.read_text(encoding="utf-8")
            self.assertEqual(document.raw_content, original)
            self.assertIn(document.content, original)
            self.assertGreaterEqual(document.word_count, 100)
            self.assertEqual(len(document.content_hash), 64)

    def test_temporal_contradiction_and_hidden_detail_survive_loading(
        self,
    ) -> None:
        regulamento = _normalize(self.by_id["regulamento_descarte"].content)
        lista = _normalize(self.by_id["lista_ecopontos"].content)
        comunicado = _normalize(self.by_id["comunicado_interdicao"].content)

        self.assertIn("Farmácia Municipal EcoSaúde", regulamento)
        self.assertIn("Rua das Palmeiras, 77", regulamento)
        self.assertIn("Parque das Acácias", lista)
        self.assertIn("pilhas e baterias", lista)
        self.assertIn("15 de março de 2026", comunicado)
        self.assertIn("1º de junho de 2026", comunicado)
        self.assertIn("deixa de aceitar pilhas e baterias", comunicado)

    def test_invalid_date_raises_validation_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = _write_document(
                Path(temporary_directory),
                "invalido.md",
                (
                    "---\n"
                    'titulo: "Documento invalido"\n'
                    'data_publicacao: "31/02/2026"\n'
                    'tema: "teste"\n'
                    "---\n\n"
                    + "palavra " * 120
                ),
            )
            with self.assertRaises(DocumentValidationError):
                load_document(path)

    def test_missing_required_metadata_raises_validation_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = _write_document(
                Path(temporary_directory),
                "sem_tema.md",
                (
                    "---\n"
                    'titulo: "Documento sem tema"\n'
                    'data_publicacao: "2026-01-01"\n'
                    "---\n\n"
                    + "palavra " * 120
                ),
            )
            with self.assertRaises(DocumentValidationError):
                load_document(path)

    def test_missing_front_matter_raises_validation_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = _write_document(
                Path(temporary_directory),
                "sem_front_matter.md",
                "texto sem metadados\n",
            )
            with self.assertRaises(DocumentValidationError):
                load_document(path)

    def test_short_document_raises_validation_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = _write_document(
                Path(temporary_directory),
                "curto.md",
                (
                    "---\n"
                    'titulo: "Documento curto"\n'
                    'data_publicacao: "2026-01-01"\n'
                    'tema: "teste"\n'
                    "---\n\n"
                    "Este documento tem poucas palavras.\n"
                ),
            )
            with self.assertRaises(DocumentValidationError):
                load_document(path)

    def test_empty_directory_raises_validation_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            with self.assertRaises(DocumentValidationError):
                load_documents(Path(temporary_directory))

    def test_missing_expected_document_raises_validation_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = _write_document(
                Path(temporary_directory),
                "documento_unico.md",
                (
                    "---\n"
                    'titulo: "Documento unico"\n'
                    'data_publicacao: "2026-01-01"\n'
                    'tema: "teste"\n'
                    "---\n\n"
                    + "palavra " * 120
                ),
            )
            documents = [load_document(path)]
            with self.assertRaises(DocumentValidationError):
                validate_expected_documents(documents)


if __name__ == "__main__":
    unittest.main()
