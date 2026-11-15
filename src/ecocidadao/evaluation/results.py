from __future__ import annotations

import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .dataset import (
    EXPECTED_QUESTION_COUNT,
    GROUND_TRUTH_STATUS,
    SIMPLE_QUESTION_COUNT,
    TRAP_QUESTION_COUNT,
    EvaluationDataset,
    EvaluationQuestion,
)

RESULT_SCHEMA_VERSION = 1
RAGAS_METRIC_NAMES = (
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_recall",
)
RESULT_STATUSES = ("executado", "pendente", "erro")


class EvaluationResultError(ValueError):
    pass


def utc_timestamp() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def empty_metrics() -> dict[str, None]:
    return {name: None for name in RAGAS_METRIC_NAMES}


def _json_number(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def normalize_metrics(metrics: dict[str, Any] | None) -> dict[str, float | None]:
    normalized = empty_metrics()
    if metrics:
        for name in RAGAS_METRIC_NAMES:
            normalized[name] = _json_number(metrics.get(name))
    return normalized


def make_question_result(
    question: EvaluationQuestion,
    *,
    generated_answer: str | None,
    contexts: Iterable[str],
    context_metadata: Iterable[dict[str, Any]],
    metrics: dict[str, Any] | None,
    status: str,
    error: str | None = None,
) -> dict[str, Any]:
    if status not in RESULT_STATUSES:
        raise EvaluationResultError(f"Status invalido: {status!r}.")

    return {
        "id": question.id,
        "category": question.category,
        "question": question.question,
        "as_of": question.as_of,
        "trap_type": question.trap_type,
        "ground_truth": question.ground_truth,
        "ground_truth_status": question.ground_truth_status,
        "reference_doc_ids": list(question.reference_doc_ids),
        "generated_answer": generated_answer,
        "contexts": [str(context) for context in contexts],
        "context_metadata": [
            dict(metadata) for metadata in context_metadata
        ],
        "metrics": normalize_metrics(metrics),
        "status": status,
        "error": error,
    }


def summarize_metrics(
    question_results: Iterable[dict[str, Any]],
) -> dict[str, float | None]:
    values: dict[str, list[float]] = {
        name: [] for name in RAGAS_METRIC_NAMES
    }
    for question_result in question_results:
        metrics = question_result.get("metrics") or {}
        for name in RAGAS_METRIC_NAMES:
            number = _json_number(metrics.get(name))
            if number is not None:
                values[name].append(number)

    return {
        name: round(sum(items) / len(items), 6) if items else None
        for name, items in values.items()
    }


def build_ragas_result(
    *,
    dataset: EvaluationDataset,
    dataset_path: Path | str,
    status: str,
    reason: str | None,
    configuration: dict[str, Any],
    question_results: list[dict[str, Any]],
    generated_at: str | None = None,
) -> dict[str, Any]:
    if status not in RESULT_STATUSES:
        raise EvaluationResultError(f"Status invalido: {status!r}.")
    if status != "executado" and not (reason and reason.strip()):
        raise EvaluationResultError(
            "Resultados pendentes ou com erro precisam informar o motivo."
        )

    payload = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "status": status,
        "reason": reason.strip() if reason else None,
        "generated_at": generated_at or utc_timestamp(),
        "dataset": {
            "source": str(dataset_path),
            "question_count": len(dataset.questions),
            "simple_question_count": dataset.simple_count,
            "trap_question_count": dataset.trap_count,
            "ground_truth_status": dataset.ground_truth_status,
        },
        "configuration": dict(configuration),
        "metrics": list(RAGAS_METRIC_NAMES),
        "summary": summarize_metrics(question_results),
        "questions": question_results,
    }
    validate_ragas_result(payload)
    return payload


def validate_ragas_result(payload: Any) -> None:
    if not isinstance(payload, dict):
        raise EvaluationResultError(
            "O resultado da avaliacao deve ser um objeto JSON."
        )
    if payload.get("schema_version") != RESULT_SCHEMA_VERSION:
        raise EvaluationResultError(
            "Versao de schema do resultado invalida."
        )

    status = payload.get("status")
    if status not in RESULT_STATUSES:
        raise EvaluationResultError(
            f"Status do resultado invalido: {status!r}."
        )
    if status != "executado":
        reason = payload.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise EvaluationResultError(
                "Resultado pendente ou com erro deve informar o motivo."
            )

    dataset = payload.get("dataset")
    if not isinstance(dataset, dict):
        raise EvaluationResultError("Campo 'dataset' invalido.")
    expected_dataset_values = {
        "question_count": EXPECTED_QUESTION_COUNT,
        "simple_question_count": SIMPLE_QUESTION_COUNT,
        "trap_question_count": TRAP_QUESTION_COUNT,
        "ground_truth_status": GROUND_TRUTH_STATUS,
    }
    for key, expected in expected_dataset_values.items():
        if dataset.get(key) != expected:
            raise EvaluationResultError(
                f"Valor invalido em dataset.{key}: {dataset.get(key)!r}."
            )

    if payload.get("metrics") != list(RAGAS_METRIC_NAMES):
        raise EvaluationResultError(
            "A lista de metricas RAGAS nao corresponde ao esperado."
        )

    questions = payload.get("questions")
    if not isinstance(questions, list):
        raise EvaluationResultError("Campo 'questions' invalido.")
    if len(questions) != EXPECTED_QUESTION_COUNT:
        raise EvaluationResultError(
            "O resultado deve conter exatamente "
            f"{EXPECTED_QUESTION_COUNT} perguntas."
        )

    required_keys = {
        "id",
        "category",
        "question",
        "as_of",
        "trap_type",
        "ground_truth",
        "ground_truth_status",
        "reference_doc_ids",
        "generated_answer",
        "contexts",
        "context_metadata",
        "metrics",
        "status",
        "error",
    }
    ids: list[str] = []
    for index, question in enumerate(questions):
        if not isinstance(question, dict):
            raise EvaluationResultError(
                f"Pergunta {index} do resultado invalida."
            )
        missing = sorted(required_keys - set(question))
        if missing:
            raise EvaluationResultError(
                f"Pergunta {index} sem campos obrigatorios: "
                + ", ".join(missing)
                + "."
            )

        question_id = question.get("id")
        if not isinstance(question_id, str) or not question_id:
            raise EvaluationResultError(
                f"Pergunta {index} com id invalido."
            )
        ids.append(question_id)

        metrics = question.get("metrics")
        if not isinstance(metrics, dict):
            raise EvaluationResultError(
                f"Pergunta {index} com metricas invalidas."
            )
        if set(metrics) != set(RAGAS_METRIC_NAMES):
            raise EvaluationResultError(
                f"Pergunta {index} nao contem todas as metricas RAGAS."
            )

        if question.get("ground_truth_status") != GROUND_TRUTH_STATUS:
            raise EvaluationResultError(
                f"Pergunta {index} com ground_truth_status invalido."
            )

        if status == "executado":
            answer = question.get("generated_answer")
            if not isinstance(answer, str) or not answer.strip():
                raise EvaluationResultError(
                    f"Pergunta {index} sem resposta gerada."
                )

    if len(ids) != len(set(ids)):
        raise EvaluationResultError(
            "Ha perguntas duplicadas no resultado da avaliacao."
        )


__all__ = [
    "RAGAS_METRIC_NAMES",
    "RESULT_SCHEMA_VERSION",
    "RESULT_STATUSES",
    "EvaluationResultError",
    "build_ragas_result",
    "empty_metrics",
    "make_question_result",
    "normalize_metrics",
    "summarize_metrics",
    "utc_timestamp",
    "validate_ragas_result",
]
