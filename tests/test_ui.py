from __future__ import annotations

import sys
import unittest
from pathlib import Path

import gradio as gr

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ecocidadao.agent import (
    AGENT_ERROR_ANSWER,
    AgentResponse,
    AgentSource,
    ChatSession,
    ConversationTurn,
    ToolCallRecord,
)
from ecocidadao.config import Settings
from ecocidadao.ui import (
    build_demo,
    display_answer,
    format_assistant_message,
    format_sources,
    format_status,
)
from ecocidadao.ui.interface import _respond


def _source() -> AgentSource:
    return AgentSource(
        label="F1",
        title="Regulamento de Descarte de Resíduos de EcoCidade",
        doc_id="regulamento_descarte",
        publication_date="2026-01-20",
        section="6. Descarte de medicamentos",
        source_file="regulamento_descarte.md",
        citation=(
            "[F1] Regulamento de Descarte de Resíduos de EcoCidade "
            "(documento: regulamento_descarte; publicado em: 2026-01-20; "
            "seção: 6. Descarte de medicamentos; "
            "arquivo: regulamento_descarte.md)"
        ),
    )


def _completed_response() -> AgentResponse:
    return AgentResponse(
        question="Onde descartar medicamentos?",
        answer="Leve os medicamentos à Farmácia Municipal EcoSaúde [F1].",
        sources=(_source(),),
        stopped_reason="completed",
    )


class PresentationTests(unittest.TestCase):
    def test_completed_answer_displays_sources(self) -> None:
        message = format_assistant_message(_completed_response())
        self.assertIn("Resposta concluída", message)
        self.assertIn("Farmácia Municipal", message)
        self.assertIn("[F1]", message)
        self.assertIn("Regulamento de Descarte", message)

    def test_guardrail_refusal_has_clear_visual_status(self) -> None:
        response = AgentResponse(
            question="Conte uma piada.",
            answer="Só posso ajudar com o domínio do EcoCidadão.",
            blocked_by_guardrail=True,
            stopped_reason="input_guardrail",
        )
        message = format_assistant_message(response)
        self.assertIn("Solicitação recusada pelos guardrails", message)
        self.assertIn("> Só posso ajudar", message)
        self.assertIn("recusada antes de consultar", format_status(response))

    def test_insufficient_context_is_explicit(self) -> None:
        response = AgentResponse(
            question="Pergunta sem base?",
            answer=(
                "Não encontrei informações suficientes para responder "
                "com segurança."
            ),
            blocked_by_guardrail=True,
            stopped_reason="insufficient_context",
        )
        message = format_assistant_message(response)
        self.assertIn("Contexto insuficiente", message)
        self.assertIn("contexto suficiente", format_status(response))

    def test_ollama_failure_has_friendly_answer(self) -> None:
        response = AgentResponse(
            question="Onde descartar pilhas?",
            answer="Erro genérico.",
            blocked_by_guardrail=True,
            stopped_reason="llm_error",
        )
        answer = display_answer(response)
        self.assertIn("Ollama local", answer)
        self.assertIn("Falha de conexão", format_assistant_message(response))

    def test_generic_agent_error_from_rag_llm_is_mapped(self) -> None:
        response = AgentResponse(
            question="Onde descartar pilhas?",
            answer=AGENT_ERROR_ANSWER,
            tool_calls=(
                ToolCallRecord(
                    name="consultar_base_documental",
                    arguments={"pergunta": "pilhas"},
                    result=(
                        "Erro controlado na consulta documental: Falha ao "
                        "consultar o modelo de linguagem."
                    ),
                    error=True,
                ),
            ),
            stopped_reason="completed",
        )
        self.assertIn("Ollama local", display_answer(response))

    def test_vector_store_failure_has_friendly_answer(self) -> None:
        response = AgentResponse(
            question="Onde descartar pilhas?",
            answer="Erro genérico.",
            tool_calls=(
                ToolCallRecord(
                    name="consultar_base_documental",
                    arguments={"pergunta": "pilhas"},
                    result=(
                        "Erro controlado na consulta documental: "
                        "chromadb indisponível."
                    ),
                    error=True,
                ),
            ),
            blocked_by_guardrail=True,
            stopped_reason="insufficient_context",
        )
        answer = display_answer(response)
        self.assertIn("banco vetorial", answer.casefold())
        self.assertIn("Base documental", format_status(response))

    def test_sources_panel_shows_tool_names_without_results(self) -> None:
        response = AgentResponse(
            question="Quantos quilos?",
            answer="O resultado estimado é 12 kg.",
            tool_calls=(
                ToolCallRecord(
                    name="calcular",
                    arguments={"expressao": "3 * 4"},
                    result="Resultado do cálculo: 12.",
                ),
            ),
            stopped_reason="completed",
        )
        sources = format_sources(response)
        self.assertIn("Nenhuma fonte documental", sources)
        self.assertIn("`calcular`", sources)
        self.assertNotIn("3 * 4", sources)


class FakeAgent:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def ask(
        self,
        question: str,
        as_of: object = None,
        history: object = None,
    ) -> AgentResponse:
        self.calls.append((question, history))
        return AgentResponse(
            question=question,
            answer=f"Resposta para {question}",
            stopped_reason="completed",
        )


class ChatSessionTests(unittest.TestCase):
    def test_session_passes_prior_turns_as_history(self) -> None:
        agent = FakeAgent()
        session = ChatSession(agent=agent, max_history_turns=2)

        session.ask("primeira")
        session.ask("segunda")
        session.ask("terceira")

        first_history = agent.calls[1][1]
        self.assertEqual(
            first_history,
            (
                ConversationTurn(
                    question="primeira",
                    answer="Resposta para primeira",
                    stopped_reason="completed",
                ),
            ),
        )
        third_history = agent.calls[2][1]
        self.assertEqual(len(third_history), 2)
        self.assertEqual(
            [turn.question for turn in third_history],
            ["primeira", "segunda"],
        )

    def test_clear_removes_history(self) -> None:
        agent = FakeAgent()
        session = ChatSession(agent=agent)
        session.ask("primeira")

        session.clear()

        self.assertEqual(session.turns, ())
        session.ask("segunda")
        self.assertEqual(agent.calls[1][1], ())


class InterfaceTests(unittest.TestCase):
    def test_respond_appends_history_and_creates_session(self) -> None:
        agent = FakeAgent()

        cleared, history, session, sources, status = _respond(
            "Onde descartar pilhas?",
            [],
            None,
            agent=agent,
            startup_error=None,
        )

        self.assertEqual(cleared, "")
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[1]["role"], "assistant")
        self.assertIn("Resposta para", history[1]["content"])
        self.assertIsInstance(session, ChatSession)
        self.assertIn("Nenhuma fonte documental", sources)
        self.assertIn("Resposta concluída", status)

    def test_build_demo_returns_blocks(self) -> None:
        demo = build_demo(
            agent=FakeAgent(),
            settings=Settings(),
            startup_error=None,
        )
        self.assertIsInstance(demo, gr.Blocks)
        demo.close()


if __name__ == "__main__":
    unittest.main()
