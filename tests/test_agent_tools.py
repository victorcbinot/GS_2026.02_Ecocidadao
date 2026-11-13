from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ecocidadao.agent import (
    EcopontoCatalog,
    build_tools,
)
from ecocidadao.rag import RagResponse, Source


class StubRagService:
    def __init__(
        self,
        response: RagResponse | None = None,
        error: Exception | None = None,
    ) -> None:
        self.response = response
        self.error = error
        self.calls: list[tuple[str, str | None]] = []

    def ask(
        self,
        question: str,
        as_of: str | None = None,
    ) -> RagResponse:
        self.calls.append((question, as_of))
        if self.error is not None:
            raise self.error
        if self.response is None:
            raise RuntimeError("resposta nao configurada")
        return self.response


def _source() -> Source:
    return Source(
        label="F1",
        chunk_id="regulamento_descarte::markdown::0001",
        doc_id="regulamento_descarte",
        title="Regulamento de Descarte de Resíduos de EcoCidade",
        publication_date="2026-01-20",
        topic="descarte",
        source_file="regulamento_descarte.md",
        section="6. Descarte de medicamentos",
        text="Medicamentos vencidos devem ser entregues na Farmácia.",
        similarity=0.91,
        metadata={"municipio": "EcoCidade"},
        dates_mentioned=(),
    )


class AgentToolsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = EcopontoCatalog.load(
            PROJECT_ROOT / "data" / "ecopontos.json"
        )

    def _tools(
        self,
        rag: StubRagService | None = None,
    ) -> dict[str, object]:
        tools = build_tools(
            rag_service=rag or StubRagService(),
            ecopontos=self.catalog,
            now_provider=lambda: date(2026, 6, 10),
        )
        return {item.name: item for item in tools}

    def test_document_tool_returns_answer_context_and_citations(self) -> None:
        source = _source()
        rag = StubRagService(
            RagResponse(
                question="Onde descartar medicamentos vencidos?",
                answer="Descarte na Farmácia Municipal EcoSaúde [F1].",
                sources=[source],
                cited_sources=[source],
                context="[F1]\nTrecho: medicamentos vencidos...",
                temporal_notes="",
                collection_name="ecocidadao_markdown",
                as_of="2026-06-10",
                has_sufficient_context=True,
            )
        )
        tool = self._tools(rag)["consultar_base_documental"]

        result = tool.invoke(
            {
                "pergunta": "Onde descartar medicamentos vencidos?",
                "data_referencia": "2026-06-10",
            }
        )

        self.assertIn("Farmácia Municipal EcoSaúde [F1]", result)
        self.assertIn("Contexto documental recuperado", result)
        self.assertIn("[F1] Regulamento de Descarte", result)
        self.assertIn("2026-06-10", result)
        self.assertEqual(rag.calls, [("Onde descartar medicamentos vencidos?", "2026-06-10")])

    def test_document_tool_returns_controlled_error(self) -> None:
        rag = StubRagService(error=RuntimeError("modelo indisponivel"))
        tool = self._tools(rag)["consultar_base_documental"]

        result = tool.invoke({"pergunta": "Onde descartar pilhas?"})

        self.assertIn("Erro controlado na consulta documental", result)
        self.assertIn("modelo indisponivel", result)

    def test_document_tool_rejects_empty_question(self) -> None:
        tool = self._tools()["consultar_base_documental"]
        result = tool.invoke({"pergunta": "   "})
        self.assertIn("não pode ser vazia", result)

    def test_ecoponto_tool_considers_interdiction_and_alternatives(self) -> None:
        tool = self._tools()["consultar_ecopontos"]
        result = tool.invoke(
            {
                "ecoponto": "Parque das Acácias",
                "material": "pilhas",
                "data_referencia": "2026-04-01",
            }
        )

        self.assertIn("Parque das Acácias: interditado", result)
        self.assertIn("Ecoponto Industrial", result)
        self.assertIn("2026-04-01", result)

    def test_ecoponto_tool_uses_reopening_rules(self) -> None:
        tool = self._tools()["consultar_ecopontos"]
        result = tool.invoke(
            {
                "material": "pilhas",
                "data_referencia": "2026-06-10",
            }
        )

        self.assertIn("Industrial", result)
        self.assertIn("não aceito", result)
        self.assertIn("08:00 às 17:00", result)

    def test_ecoponto_tool_rejects_invalid_date(self) -> None:
        tool = self._tools()["consultar_ecopontos"]
        result = tool.invoke({"data_referencia": "10/06/2026"})
        self.assertIn("Erro controlado", result)

    def test_calculator_tool_returns_estimate_disclaimer(self) -> None:
        tool = self._tools()["calcular"]
        result = tool.invoke({"expressao": "50 * 4"})
        self.assertIn("200", result)
        self.assertIn("não um dado oficial", result)

    def test_calculator_tool_rejects_unsafe_code(self) -> None:
        tool = self._tools()["calcular"]
        result = tool.invoke({"expressao": "__import__('os')"})
        self.assertIn("Erro controlado na calculadora", result)

    def test_current_date_tool_uses_injected_date(self) -> None:
        tool = self._tools()["data_atual"]
        self.assertEqual(tool.invoke({}), "Data atual: 2026-06-10")


if __name__ == "__main__":
    unittest.main()
