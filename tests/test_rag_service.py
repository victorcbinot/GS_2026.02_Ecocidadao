from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from ecocidadao.ingestion import Chunk
    from ecocidadao.rag import (
        COLLECTION_FIXO,
        COLLECTION_MARKDOWN,
        NO_CONTEXT_ANSWER,
        ChromaVectorStore,
        RagService,
        RagServiceError,
        is_temporal_question,
    )

    RAG_SERVICE_AVAILABLE = True
except ImportError as error:
    RAG_SERVICE_AVAILABLE = False
    RAG_SERVICE_IMPORT_ERROR = error


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
            0.01 + float("maca" in lower or "planta" in lower),
        ]


def _make_chunk(
    chunk_id: str,
    text: str,
    doc_id: str,
    title: str,
    publication_date: str,
    section: str,
    strategy: str = "fixo",
    index: int = 0,
) -> Chunk:
    metadata = {
        "doc_id": doc_id,
        "titulo": title,
        "data_publicacao": publication_date,
        "tema": "descarte",
        "municipio": "EcoCidade",
        "orgao": "Secretaria de Meio Ambiente",
        "versao": "1.0",
        "source_file": f"{doc_id}.md",
        "section_path": ["Regulamento", section],
        "section_path_text": f"Regulamento > {section}",
        "chunk_id": chunk_id,
        "chunk_index": index,
        "chunk_strategy": strategy,
        "char_count": len(text),
        "word_count": len(text.split()),
        "chunk_content_hash": f"hash-{chunk_id}",
        "document_content_hash": f"doc-{doc_id}",
        "section_h1": "Regulamento",
        "section_h2": section,
        "section_h3": None,
        "section_level": 2,
    }
    return Chunk(
        chunk_id=chunk_id,
        doc_id=doc_id,
        text=text,
        metadata=metadata,
        chunk_index=index,
    )


class EmptyStore:
    def count(self) -> int:
        return 0

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        where: dict[str, object] | None = None,
    ) -> list[object]:
        return []


class RecordingLLM:
    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.prompts: list[str] = []

    def __call__(self, prompt_value: object) -> AIMessage:
        if hasattr(prompt_value, "to_string"):
            self.prompts.append(prompt_value.to_string())
        else:
            self.prompts.append(str(prompt_value))
        return AIMessage(content=self.answer)

    @property
    def runnable(self) -> RunnableLambda:
        return RunnableLambda(self)


@unittest.skipUnless(
    RAG_SERVICE_AVAILABLE,
    "Dependencias do servico RAG nao instaladas.",
)
class RagServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(
            tempfile.mkdtemp(prefix="ecocidadao-rag-test-")
        )
        self.embedding_model = FakeEmbeddingModel()
        self.chunks = {
            "fixo": [
                _make_chunk(
                    chunk_id="lista_ecopontos::fixo::0001",
                    text=(
                        "O Parque das Acácias aceita pilhas e baterias e "
                        "funciona de segunda a sábado, das 07:00 às 19:00."
                    ),
                    doc_id="lista_ecopontos",
                    title="Lista de Ecopontos de EcoCidade",
                    publication_date="2026-02-01",
                    section="Parque das Acácias",
                    index=1,
                ),
                _make_chunk(
                    chunk_id="comunicado_interdicao::fixo::0002",
                    text=(
                        "A partir de 1º de junho de 2026, o Parque das "
                        "Acácias deixa de aceitar pilhas e baterias. O "
                        "Ecoponto Industrial passa a receber esses materiais. "
                        "Horário: segunda a sexta, 08:00 às 17:00; sábado, "
                        "08:00 às 12:00."
                    ),
                    doc_id="comunicado_interdicao",
                    title="Comunicado de Interdição do Ecoponto Parque das Acácias",
                    publication_date="2026-03-10",
                    section="3. Reabertura e mudanças permanentes",
                    index=2,
                ),
                _make_chunk(
                    chunk_id="regulamento_descarte::fixo::0006",
                    text=(
                        "Medicamentos vencidos devem ser entregues na "
                        "Farmácia Municipal EcoSaúde, Rua das Palmeiras, "
                        "77, Centro, segunda a sexta, 08:00 às 17:00."
                    ),
                    doc_id="regulamento_descarte",
                    title="Regulamento de Descarte de Resíduos de EcoCidade",
                    publication_date="2026-01-20",
                    section="6. Descarte de medicamentos",
                    index=6,
                ),
            ],
            "markdown": [
                _make_chunk(
                    chunk_id="lista_ecopontos::markdown::0001",
                    text="Texto recuperado da colecao markdown sobre pilhas.",
                    doc_id="lista_ecopontos",
                    title="Lista de Ecopontos de EcoCidade",
                    publication_date="2026-02-01",
                    section="Parque das Acácias",
                    strategy="markdown",
                    index=1,
                ),
                _make_chunk(
                    chunk_id="comunicado_interdicao::markdown::0002",
                    text="Texto recuperado da colecao markdown sobre pilhas.",
                    doc_id="comunicado_interdicao",
                    title="Comunicado de Interdição",
                    publication_date="2026-03-10",
                    section="3. Reabertura",
                    strategy="markdown",
                    index=2,
                ),
            ],
        }
        self.stores = {}
        for strategy, collection_name in (
            ("fixo", COLLECTION_FIXO),
            ("markdown", COLLECTION_MARKDOWN),
        ):
            store = ChromaVectorStore(
                collection_name=collection_name,
                chroma_dir=self.temp_dir,
                embedding_model=self.embedding_model,
            )
            store.create_or_update(self.chunks[strategy])
            self.stores[collection_name] = store

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _service(self, llm: RecordingLLM, **kwargs: object) -> RagService:
        kwargs.setdefault("collection_name", COLLECTION_FIXO)
        return RagService(
            llm=llm.runnable,
            vector_store_factory=lambda name: self.stores[name],
            now_provider=lambda: date(2026, 11, 13),
            **kwargs,
        )

    def test_retrieval_uses_selected_collection(self) -> None:
        service = self._service(
            RecordingLLM("resposta [F1]"),
            collection_name=COLLECTION_MARKDOWN,
        )
        retrieved = service.retrieve("pilhas", collection_name=COLLECTION_MARKDOWN)

        self.assertTrue(retrieved)
        self.assertTrue(
            all(
                "::markdown::" in result.chunk_id
                for result in retrieved
            )
        )

    def test_answer_returns_citations_and_source_metadata(self) -> None:
        llm = RecordingLLM("Resposta documental [F1].")
        service = self._service(llm, top_k=1)

        response = service.ask(
            "Onde descartar medicamentos vencidos?",
            as_of="2026-06-10",
        )

        self.assertEqual(response.answer, "Resposta documental [F1].")
        self.assertTrue(response.has_sufficient_context)
        self.assertEqual(len(response.sources), 1)
        self.assertEqual(response.sources[0].doc_id, "regulamento_descarte")
        self.assertEqual(len(response.cited_sources), 1)
        self.assertEqual(
            response.cited_sources[0].chunk_id,
            response.sources[0].chunk_id,
        )
        self.assertIn(
            "Farmácia Municipal EcoSaúde",
            response.sources[0].text,
        )
        self.assertIn("[F1]", llm.prompts[0])
        self.assertIn("Medicamentos vencidos", llm.prompts[0])

    def test_no_context_does_not_call_llm(self) -> None:
        llm = RecordingLLM("resposta [F1]")
        service = RagService(
            llm=llm.runnable,
            collection_name=COLLECTION_FIXO,
            vector_store_factory=lambda name: EmptyStore(),
            now_provider=lambda: date(2026, 11, 13),
            top_k=2,
        )

        response = service.ask("Onde descartar pilhas?")

        self.assertEqual(response.answer, NO_CONTEXT_ANSWER)
        self.assertFalse(response.has_sufficient_context)
        self.assertEqual(response.sources, [])
        self.assertEqual(response.cited_sources, [])
        self.assertEqual(llm.prompts, [])
        self.assertIn("insufficient_context", response.guardrail_events)

    def test_temporal_prompt_contains_both_rules_and_reference_date(self) -> None:
        llm = RecordingLLM("Resposta [F1] [F2].")
        service = self._service(
            llm,
            top_k=2,
            score_threshold=0.0,
        )

        response = service.ask(
            "O Parque das Acácias aceita pilhas em 10/06/2026?",
            as_of="2026-06-10",
        )

        prompt = llm.prompts[0]
        self.assertIn("2026-06-10", prompt)
        self.assertIn("2026-02-01", prompt)
        self.assertIn("2026-03-10", prompt)
        self.assertIn("1º de junho de 2026", prompt)
        self.assertIn("10/06/2026", prompt)
        self.assertIn("Não misture regras antigas e novas", prompt)
        self.assertIn("deixa de aceitar pilhas e baterias", prompt)
        self.assertEqual(response.as_of, "2026-06-10")
        self.assertGreaterEqual(len(response.sources), 2)

    def test_temporal_question_expands_retrieval_window(self) -> None:
        service = self._service(
            RecordingLLM("Resposta [F1]."),
            top_k=2,
            score_threshold=0.0,
        )

        self.assertTrue(
            is_temporal_question(
                "O Parque das Acácias aceita pilhas em 10/06/2026?"
            )
        )
        self.assertFalse(
            is_temporal_question("Onde descartar medicamentos vencidos?")
        )
        retrieved = service.retrieve(
            "O Parque das Acácias aceita pilhas em 10/06/2026?"
        )
        self.assertEqual(len(retrieved), 3)

    def test_invalid_collection_is_rejected(self) -> None:
        service = self._service(RecordingLLM("resposta [F1]"))

        with self.assertRaises(ValueError):
            service.ask("pilhas", collection_name="colecao_invalida")

    def test_empty_question_is_rejected(self) -> None:
        service = self._service(RecordingLLM("resposta [F1]"))

        with self.assertRaises(ValueError):
            service.ask("   ")

    def test_llm_failure_is_wrapped_in_service_error(self) -> None:
        failing_llm = RunnableLambda(
            lambda prompt_value: (_ for _ in ()).throw(
                RuntimeError("falha simulada")
            )
        )
        service = RagService(
            llm=failing_llm,
            collection_name=COLLECTION_FIXO,
            vector_store_factory=lambda name: self.stores[name],
            now_provider=lambda: date(2026, 11, 13),
            top_k=1,
        )

        with self.assertRaises(RagServiceError):
            service.ask("Onde descartar medicamentos?")

    def test_response_to_dict_contains_sources(self) -> None:
        service = self._service(
            RecordingLLM("Resposta [F1]."),
            top_k=1,
        )
        response = service.ask("Onde descartar medicamentos?")
        data = response.to_dict()

        self.assertEqual(data["answer"], "Resposta [F1].")
        self.assertEqual(data["collection_name"], COLLECTION_FIXO)
        self.assertEqual(len(data["sources"]), 1)
        self.assertIn("metadata", data["sources"][0])


if __name__ == "__main__":
    unittest.main()
