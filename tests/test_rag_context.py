from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from ecocidadao.rag import (
        RetrievedChunk,
        build_context,
        extract_date_mentions,
    )

    RAG_CONTEXT_AVAILABLE = True
except ImportError as error:
    RAG_CONTEXT_AVAILABLE = False
    RAG_CONTEXT_IMPORT_ERROR = error


def _chunk(
    chunk_id: str,
    text: str,
    doc_id: str,
    title: str,
    publication_date: str,
    section: str,
    similarity: float = 0.8,
) -> RetrievedChunk:
    metadata = {
        "doc_id": doc_id,
        "titulo": title,
        "data_publicacao": publication_date,
        "tema": "descarte",
        "source_file": f"{doc_id}.md",
        "section_path": ["Regulamento", section],
        "section_path_text": f"Regulamento > {section}",
        "municipio": "EcoCidade",
        "orgao": "Secretaria de Meio Ambiente",
        "versao": "1.0",
        "chunk_id": chunk_id,
        "chunk_strategy": "markdown",
    }
    return RetrievedChunk(
        chunk_id=chunk_id,
        text=text,
        metadata=metadata,
        distance=1.0 - similarity,
        similarity=similarity,
    )


@unittest.skipUnless(
    RAG_CONTEXT_AVAILABLE,
    "Dependencias do servico RAG nao instaladas.",
)
class RagContextTests(unittest.TestCase):
    def setUp(self) -> None:
        self.old_rule = _chunk(
            chunk_id="lista::0001",
            text=(
                "O Parque das Acácias aceita pilhas e baterias e funciona "
                "de segunda a sábado, das 07:00 às 19:00."
            ),
            doc_id="lista_ecopontos",
            title="Lista de Ecopontos de EcoCidade",
            publication_date="2026-02-01",
            section="Parque das Acácias",
            similarity=0.91,
        )
        self.new_rule = _chunk(
            chunk_id="comunicado::0003",
            text=(
                "A partir de 1º de junho de 2026, o Parque das Acácias "
                "deixa de aceitar pilhas e baterias. O Ecoponto Industrial "
                "passa a receber esses materiais."
            ),
            doc_id="comunicado_interdicao",
            title="Comunicado de Interdição do Ecoponto Parque das Acácias",
            publication_date="2026-03-10",
            section="3. Reabertura e mudanças permanentes",
            similarity=0.88,
        )

    def test_extract_date_mentions_finds_document_dates(self) -> None:
        text = (
            "Interdição de 15 de março de 2026 a 31 de maio de 2026; "
            "reabertura em 1º de junho de 2026; publicado em 10/03/2026; "
            "referência 2026-06-10."
        )
        mentions = extract_date_mentions(text)

        self.assertIn("15 de março de 2026", mentions)
        self.assertIn("31 de maio de 2026", mentions)
        self.assertIn("1º de junho de 2026", mentions)
        self.assertIn("10/03/2026", mentions)
        self.assertIn("2026-06-10", mentions)

    def test_context_includes_citation_metadata_and_temporal_notes(self) -> None:
        bundle = build_context(
            question=(
                "O Parque das Acácias aceita pilhas em 10/06/2026?"
            ),
            retrieved=[self.old_rule, self.new_rule],
            as_of=date(2026, 6, 10),
            max_chars=10000,
        )

        self.assertEqual(len(bundle.sources), 2)
        self.assertEqual(bundle.sources[0].label, "F1")
        self.assertEqual(bundle.sources[0].doc_id, "lista_ecopontos")
        self.assertEqual(
            bundle.sources[0].title,
            "Lista de Ecopontos de EcoCidade",
        )
        self.assertEqual(bundle.sources[0].publication_date, "2026-02-01")
        self.assertIn("[F1]", bundle.text)
        self.assertIn("Lista de Ecopontos de EcoCidade", bundle.text)
        self.assertIn("Publicado em: 2026-02-01", bundle.text)
        self.assertIn("Parque das Acácias", bundle.text)
        self.assertIn("10/06/2026", bundle.temporal_notes)
        self.assertIn("2026-06-10", bundle.temporal_notes)
        self.assertIn("Não misture regras antigas e novas", bundle.temporal_notes)
        self.assertIn("1º de junho de 2026", bundle.temporal_notes)
        self.assertIn("2026-03-10", bundle.temporal_notes)

    def test_citation_contains_document_name_title_date_and_section(self) -> None:
        bundle = build_context(
            question="Onde descartar medicamentos?",
            retrieved=[self.new_rule],
            as_of="2026-06-10",
        )
        citation = bundle.sources[0].citation()

        self.assertIn("[F1]", citation)
        self.assertIn("Comunicado de Interdição", citation)
        self.assertIn("comunicado_interdicao", citation)
        self.assertIn("2026-03-10", citation)
        self.assertIn("3. Reabertura", citation)
        self.assertIn("comunicado_interdicao.md", citation)

    def test_context_respects_maximum_character_limit(self) -> None:
        bundle = build_context(
            question="pilhas",
            retrieved=[self.old_rule, self.new_rule],
            as_of="2026-06-10",
            max_chars=300,
        )

        self.assertLessEqual(len(bundle.text), 300)
        self.assertEqual(len(bundle.sources), 1)

    def test_empty_context_is_reported_explicitly(self) -> None:
        bundle = build_context(
            question="Como plantar macieiras?",
            retrieved=[],
            as_of="2026-06-10",
        )

        self.assertEqual(bundle.text, "")
        self.assertEqual(bundle.sources, [])
        self.assertIsNone(bundle.source_by_label("F1"))
        self.assertIn("Data de referência: 2026-06-10", bundle.temporal_notes)


if __name__ == "__main__":
    unittest.main()
