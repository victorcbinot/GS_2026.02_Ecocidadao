from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ecocidadao.evaluation import (
    EvaluationDatasetError,
    build_ragas_result,
    compute_ranking_metrics,
    load_evaluation_dataset,
    make_question_result,
    parse_evaluation_dataset,
    validate_chunking_experiment,
    validate_ragas_result,
)

DATASET_PATH = PROJECT_ROOT / "src" / "ecocidadao" / "evaluation" / "dataset.json"
RAGAS_RESULT_PATH = PROJECT_ROOT / "avaliacao_ragas.json"
CHUNKING_EXPERIMENT_PATH = (
    PROJECT_ROOT / "data" / "experiments" / "chunking_comparison.json"
)


class EvaluationDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dataset = load_evaluation_dataset(DATASET_PATH)

    def test_dataset_has_exactly_eight_questions_and_balanced_categories(
        self,
    ) -> None:
        self.assertEqual(len(self.dataset.questions), 8)
        self.assertEqual(self.dataset.simple_count, 4)
        self.assertEqual(self.dataset.trap_count, 4)

    def test_question_ids_are_unique(self) -> None:
        ids = [question.id for question in self.dataset.questions]
        self.assertEqual(len(ids), len(set(ids)))

    def test_ground_truths_are_human_validated(self) -> None:
        self.assertEqual(
            self.dataset.ground_truth_status,
            "validado_humanamente",
        )
        for question in self.dataset.questions:
            self.assertEqual(
                question.ground_truth_status,
                "validado_humanamente",
            )
            self.assertTrue(question.ground_truth.strip())

    def test_dataset_rejects_pending_ground_truths(self) -> None:
        payload = self.dataset.to_dict()
        payload["ground_truth_status"] = "pendente_validacao_humana"
        payload["questions"][0]["ground_truth_status"] = (
            "pendente_validacao_humana"
        )

        with self.assertRaises(EvaluationDatasetError):
            parse_evaluation_dataset(payload)

    def test_trap_questions_declare_a_conflict_type(self) -> None:
        for question in self.dataset.questions:
            if question.category == "armadilha":
                self.assertTrue(question.trap_type)
            else:
                self.assertIsNone(question.trap_type)

    def test_every_question_has_references_and_answer_points(self) -> None:
        for question in self.dataset.questions:
            self.assertTrue(question.reference_doc_ids)
            self.assertTrue(question.reference_sections)
            self.assertTrue(question.expected_answer_points)

    def test_dataset_rejects_wrong_question_count(self) -> None:
        payload = self.dataset.to_dict()
        payload["questions"] = payload["questions"][:-1]

        with self.assertRaises(EvaluationDatasetError):
            parse_evaluation_dataset(payload)


class RankingMetricsTests(unittest.TestCase):
    def test_hit_and_mrr_for_relevant_document(self) -> None:
        metrics = compute_ranking_metrics(
            ranked_doc_ids=["doc_a", "doc_b", "doc_c"],
            relevant_doc_ids=["doc_b"],
        )

        self.assertTrue(metrics["hit_at_3"])
        self.assertTrue(metrics["hit_at_5"])
        self.assertEqual(metrics["first_relevant_rank"], 2)
        self.assertEqual(metrics["mrr"], 0.5)
        self.assertEqual(metrics["relevant_retrieved"], ["doc_b"])
        self.assertEqual(metrics["missing_relevant"], [])

    def test_hit_at_3_can_fail_while_hit_at_5_passes(self) -> None:
        metrics = compute_ranking_metrics(
            ranked_doc_ids=[
                "doc_a",
                "doc_b",
                "doc_c",
                "doc_d",
                "doc_e",
            ],
            relevant_doc_ids=["doc_e"],
        )

        self.assertFalse(metrics["hit_at_3"])
        self.assertTrue(metrics["hit_at_5"])
        self.assertEqual(metrics["first_relevant_rank"], 5)
        self.assertEqual(metrics["mrr"], 0.2)

    def test_no_relevant_document_scores_zero(self) -> None:
        metrics = compute_ranking_metrics(
            ranked_doc_ids=["doc_a", "doc_b"],
            relevant_doc_ids=["doc_c"],
        )

        self.assertFalse(metrics["hit_at_3"])
        self.assertFalse(metrics["hit_at_5"])
        self.assertIsNone(metrics["first_relevant_rank"])
        self.assertEqual(metrics["mrr"], 0.0)
        self.assertEqual(metrics["missing_relevant"], ["doc_c"])


class EvaluationResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dataset = load_evaluation_dataset(DATASET_PATH)

    def _pending_result(self) -> dict:
        question_results = [
            make_question_result(
                question,
                generated_answer=None,
                contexts=["contexto recuperado"],
                context_metadata=[{"chunk_id": "chunk-1"}],
                metrics=None,
                status="pendente",
                error="Falha externa simulada.",
            )
            for question in self.dataset.questions
        ]
        return build_ragas_result(
            dataset=self.dataset,
            dataset_path=DATASET_PATH,
            status="pendente",
            reason="Falha externa simulada.",
            configuration={"collection_name": "ecocidadao_markdown"},
            question_results=question_results,
        )

    def test_pending_result_has_required_question_fields(self) -> None:
        payload = self._pending_result()
        validate_ragas_result(payload)

        self.assertEqual(payload["status"], "pendente")
        self.assertEqual(len(payload["questions"]), 8)
        for question in payload["questions"]:
            self.assertIn("generated_answer", question)
            self.assertIn("contexts", question)
            self.assertIn("ground_truth", question)
            self.assertIn("metrics", question)
            self.assertIsNone(question["generated_answer"])
            self.assertIsNone(question["metrics"]["faithfulness"])

    def test_pending_result_requires_reason(self) -> None:
        payload = copy.deepcopy(self._pending_result())
        payload["reason"] = None

        with self.assertRaises(ValueError):
            validate_ragas_result(payload)

    def test_executed_result_requires_generated_answers(self) -> None:
        payload = copy.deepcopy(self._pending_result())
        payload["status"] = "executado"
        payload["reason"] = None

        with self.assertRaises(ValueError):
            validate_ragas_result(payload)

    def test_generated_ragas_file_has_valid_schema(self) -> None:
        if not RAGAS_RESULT_PATH.is_file():
            self.skipTest("avaliacao_ragas.json ainda nao foi gerado.")

        payload = json.loads(RAGAS_RESULT_PATH.read_text(encoding="utf-8"))
        validate_ragas_result(payload)
        self.assertIn(payload["status"], {"executado", "pendente", "erro"})
        self.assertEqual(len(payload["questions"]), 8)


class ChunkingExperimentTests(unittest.TestCase):
    def test_generated_chunking_experiment_has_valid_schema(self) -> None:
        if not CHUNKING_EXPERIMENT_PATH.is_file():
            self.skipTest(
                "chunking_comparison.json ainda nao foi gerado."
            )

        payload = json.loads(
            CHUNKING_EXPERIMENT_PATH.read_text(encoding="utf-8")
        )
        validate_chunking_experiment(payload)

        self.assertIsNone(payload["winner"])
        self.assertEqual(payload["recommended_strategy"], "markdown")
        self.assertTrue(payload["recommendation_reason"])
        self.assertEqual(
            {item["strategy"] for item in payload["strategies"]},
            {"fixo", "markdown"},
        )
        for strategy in payload["strategies"]:
            self.assertEqual(
                len(strategy["retrieval"]["questions"]),
                8,
            )
            self.assertIn(
                "mean_hit_at_3",
                strategy["retrieval"]["metrics"],
            )
            self.assertIsNone(
                strategy["retrieval"]["ragas_context_precision"]
            )
            self.assertIsNone(
                strategy["retrieval"]["ragas_context_recall"]
            )


if __name__ == "__main__":
    unittest.main()
