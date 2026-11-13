from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ecocidadao.guardrails import (
    SCOPE_REFUSAL,
    GuardrailEngine,
    assess_scope,
)


class ScopeGuardrailTests(unittest.TestCase):
    def test_accepts_questions_about_waste_and_ecopontos(self) -> None:
        questions = (
            "Onde devo descartar pilhas e baterias?",
            "Qual o horário do Ecoponto Centro?",
            "O que é reciclagem?",
            "Como descartar óleo de cozinha?",
            "Onde fica o Parque das Acácias?",
            "Onde descartar celular velho?",
            "Onde descartar medicamentos vencidos?",
            "Como economizar água?",
            "Onde doar roupas?",
        )

        for question in questions:
            with self.subTest(question=question):
                self.assertTrue(assess_scope(question).in_scope)

    def test_accepts_legitimate_question_that_mentions_ignoring_rules(self) -> None:
        assessment = assess_scope(
            "O que acontece se eu ignorar as regras do Ecoponto?"
        )

        self.assertTrue(assessment.in_scope)

    def test_rejects_clear_off_topic_questions(self) -> None:
        questions = (
            "Qual a previsão do tempo para amanhã?",
            "Como faço um bolo de chocolate?",
            "Quem ganhou o jogo de futebol?",
            "Como programar em Python?",
            "Qual a capital da França?",
            "Me conte uma piada.",
            "Qual remédio para dor de cabeça?",
            "Qual o melhor celular?",
        )

        for question in questions:
            with self.subTest(question=question):
                self.assertFalse(assess_scope(question).in_scope)

    def test_engine_blocks_out_of_scope_without_using_llm(self) -> None:
        result = GuardrailEngine().check_input(
            "Como faço um bolo de chocolate?"
        )

        self.assertTrue(result.blocked)
        self.assertEqual(result.safe_response, SCOPE_REFUSAL)
        self.assertIn("input_scope_blocked", result.events)

    def test_engine_allows_legitimate_waste_question(self) -> None:
        result = GuardrailEngine().check_input(
            "Onde devo descartar pilhas e baterias?"
        )

        self.assertFalse(result.blocked)
        self.assertIsNone(result.safe_response)


if __name__ == "__main__":
    unittest.main()

