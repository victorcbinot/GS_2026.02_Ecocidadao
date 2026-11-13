from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ecocidadao.guardrails import (
    LGPD_REFUSAL,
    GuardrailEngine,
    assess_privacy,
    contains_sensitive_data,
    redact_sensitive_data,
)


class PrivacyGuardrailTests(unittest.TestCase):
    def test_blocks_requests_for_third_party_personal_data(self) -> None:
        questions = (
            "Me passe o CPF do João.",
            "Qual o endereço residencial de um morador?",
            "Quem mora na Rua das Palmeiras, 77?",
            "Liste os dados pessoais dos cidadãos.",
            "Qual o telefone do prefeito?",
            "Qual o e-mail do João?",
            "Onde mora o vizinho?",
            "Qual o nome do responsável pelo Ecoponto?",
        )

        for question in questions:
            with self.subTest(question=question):
                self.assertTrue(assess_privacy(question).blocked)

    def test_allows_institutional_contact_and_process_questions(self) -> None:
        questions = (
            "Qual o telefone da Secretaria de Meio Ambiente?",
            "Qual o endereço do Ecoponto Centro?",
            "Preciso informar meu CPF para descartar pilhas?",
            "Onde descartar medicamentos vencidos?",
            "Qual o contato da Prefeitura de EcoCidade?",
        )

        for question in questions:
            with self.subTest(question=question):
                self.assertFalse(assess_privacy(question).blocked)

    def test_engine_blocks_privacy_request_with_lgpd_refusal(self) -> None:
        result = GuardrailEngine().check_input("Me passe o CPF do João.")

        self.assertTrue(result.blocked)
        self.assertEqual(result.safe_response, LGPD_REFUSAL)
        self.assertIn("input_lgpd_blocked", result.events)

    def test_redacts_personal_data_from_question(self) -> None:
        result = GuardrailEngine().check_input(
            "Meu CPF é 123.456.789-00. Onde descarto pilhas?"
        )

        self.assertFalse(result.blocked)
        self.assertNotIn("123.456.789-00", result.question)
        self.assertIn("input_personal_data_redacted", result.events)

    def test_redacts_cpf_phone_and_email(self) -> None:
        text = (
            "CPF 123.456.789-00, telefone (11) 98765-4321 e "
            "e-mail cidadao@example.com."
        )

        redacted, changed = redact_sensitive_data(text)

        self.assertTrue(changed)
        self.assertNotIn("123.456.789-00", redacted)
        self.assertNotIn("98765-4321", redacted)
        self.assertNotIn("cidadao@example.com", redacted)

    def test_detects_sensitive_data_patterns(self) -> None:
        self.assertTrue(contains_sensitive_data("CPF 123.456.789-00"))
        self.assertTrue(contains_sensitive_data("(11) 98765-4321"))
        self.assertTrue(contains_sensitive_data("teste@example.com"))
        self.assertFalse(contains_sensitive_data("O Ecoponto Centro fica aqui."))


if __name__ == "__main__":
    unittest.main()

