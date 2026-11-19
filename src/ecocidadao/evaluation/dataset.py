from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Literal

from ..ingestion.loader import EXPECTED_DOCUMENT_IDS

DATASET_SCHEMA_VERSION = 1
EXPECTED_QUESTION_COUNT = 8
SIMPLE_QUESTION_COUNT = 4
TRAP_QUESTION_COUNT = 4
GROUND_TRUTH_STATUS = "validado_humanamente"
Category = Literal["simples", "armadilha"]


class EvaluationDatasetError(ValueError):
    pass


@dataclass(frozen=True)
class EvaluationQuestion:
    id: str
    category: Category
    question: str
    as_of: str
    trap_type: str | None
    ground_truth: str
    ground_truth_status: str
    reference_doc_ids: tuple[str, ...]
    reference_sections: tuple[str, ...]
    expected_answer_points: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "question": self.question,
            "as_of": self.as_of,
            "trap_type": self.trap_type,
            "ground_truth": self.ground_truth,
            "ground_truth_status": self.ground_truth_status,
            "reference_doc_ids": list(self.reference_doc_ids),
            "reference_sections": list(self.reference_sections),
            "expected_answer_points": list(self.expected_answer_points),
        }


@dataclass(frozen=True)
class EvaluationDataset:
    schema_version: int
    description: str
    ground_truth_status: str
    questions: tuple[EvaluationQuestion, ...]

    @property
    def simple_count(self) -> int:
        return sum(
            question.category == "simples" for question in self.questions
        )

    @property
    def trap_count(self) -> int:
        return sum(
            question.category == "armadilha" for question in self.questions
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "description": self.description,
            "ground_truth_status": self.ground_truth_status,
            "questions": [
                question.to_dict() for question in self.questions
            ],
        }


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvaluationDatasetError(
            f"Campo obrigatorio vazio ou invalido: {field}."
        )
    return value.strip()


def _require_text_list(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise EvaluationDatasetError(
            f"Campo obrigatorio deve ser uma lista nao vazia: {field}."
        )

    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise EvaluationDatasetError(
                f"Item invalido em {field}: {item!r}."
            )
        result.append(item.strip())
    return tuple(result)


def _validate_iso_date(value: Any, field: str) -> str:
    text = _require_text(value, field)
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError as error:
        raise EvaluationDatasetError(
            f"Data invalida em {field}: {text!r}."
        ) from error


def _parse_question(
    payload: Any,
    index: int,
) -> EvaluationQuestion:
    if not isinstance(payload, dict):
        raise EvaluationDatasetError(
            f"A pergunta na posicao {index} deve ser um objeto."
        )

    category = _require_text(payload.get("category"), "category")
    if category not in ("simples", "armadilha"):
        raise EvaluationDatasetError(
            f"Categoria invalida na pergunta {index}: {category!r}."
        )

    trap_type = payload.get("trap_type")
    if category == "armadilha":
        trap_type = _require_text(trap_type, f"questions[{index}].trap_type")
    elif trap_type is not None:
        raise EvaluationDatasetError(
            f"Pergunta simples na posicao {index} nao deve ter trap_type."
        )

    ground_truth_status = _require_text(
        payload.get("ground_truth_status"),
        f"questions[{index}].ground_truth_status",
    )
    if ground_truth_status != GROUND_TRUTH_STATUS:
        raise EvaluationDatasetError(
            "Os ground truths devem estar marcados como "
            f"{GROUND_TRUTH_STATUS!r}."
        )

    reference_doc_ids = _require_text_list(
        payload.get("reference_doc_ids"),
        f"questions[{index}].reference_doc_ids",
    )
    unknown_doc_ids = sorted(
        set(reference_doc_ids) - set(EXPECTED_DOCUMENT_IDS)
    )
    if unknown_doc_ids:
        raise EvaluationDatasetError(
            "Documentos de referencia desconhecidos na pergunta "
            f"{index}: {', '.join(unknown_doc_ids)}."
        )

    return EvaluationQuestion(
        id=_require_text(payload.get("id"), f"questions[{index}].id"),
        category=category,
        question=_require_text(
            payload.get("question"),
            f"questions[{index}].question",
        ),
        as_of=_validate_iso_date(
            payload.get("as_of"),
            f"questions[{index}].as_of",
        ),
        trap_type=trap_type,
        ground_truth=_require_text(
            payload.get("ground_truth"),
            f"questions[{index}].ground_truth",
        ),
        ground_truth_status=ground_truth_status,
        reference_doc_ids=reference_doc_ids,
        reference_sections=_require_text_list(
            payload.get("reference_sections"),
            f"questions[{index}].reference_sections",
        ),
        expected_answer_points=_require_text_list(
            payload.get("expected_answer_points"),
            f"questions[{index}].expected_answer_points",
        ),
    )


def parse_evaluation_dataset(payload: Any) -> EvaluationDataset:
    if not isinstance(payload, dict):
        raise EvaluationDatasetError(
            "O dataset de avaliacao deve ser um objeto JSON."
        )

    schema_version = payload.get("schema_version")
    if schema_version != DATASET_SCHEMA_VERSION:
        raise EvaluationDatasetError(
            "Versao de schema do dataset invalida: "
            f"{schema_version!r}."
        )

    ground_truth_status = _require_text(
        payload.get("ground_truth_status"),
        "ground_truth_status",
    )
    if ground_truth_status != GROUND_TRUTH_STATUS:
        raise EvaluationDatasetError(
            "O dataset deve indicar "
            f"ground_truth_status={GROUND_TRUTH_STATUS!r}."
        )

    raw_questions = payload.get("questions")
    if not isinstance(raw_questions, list):
        raise EvaluationDatasetError(
            "O campo 'questions' deve ser uma lista."
        )
    if len(raw_questions) != EXPECTED_QUESTION_COUNT:
        raise EvaluationDatasetError(
            "O dataset deve ter exatamente "
            f"{EXPECTED_QUESTION_COUNT} perguntas; recebeu "
            f"{len(raw_questions)}."
        )

    questions = tuple(
        _parse_question(item, index)
        for index, item in enumerate(raw_questions)
    )
    ids = [question.id for question in questions]
    if len(ids) != len(set(ids)):
        raise EvaluationDatasetError(
            "Ha perguntas com id duplicado no dataset."
        )

    dataset = EvaluationDataset(
        schema_version=DATASET_SCHEMA_VERSION,
        description=_require_text(
            payload.get("description"),
            "description",
        ),
        ground_truth_status=ground_truth_status,
        questions=questions,
    )

    if dataset.simple_count != SIMPLE_QUESTION_COUNT:
        raise EvaluationDatasetError(
            "O dataset deve ter exatamente "
            f"{SIMPLE_QUESTION_COUNT} perguntas simples."
        )
    if dataset.trap_count != TRAP_QUESTION_COUNT:
        raise EvaluationDatasetError(
            "O dataset deve ter exatamente "
            f"{TRAP_QUESTION_COUNT} perguntas de armadilha."
        )

    return dataset


def load_evaluation_dataset(path: Path | str) -> EvaluationDataset:
    dataset_path = Path(path)
    if not dataset_path.is_file():
        raise FileNotFoundError(
            f"Dataset de avaliacao nao encontrado: {dataset_path}"
        )

    try:
        payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise EvaluationDatasetError(
            f"Dataset de avaliacao com JSON invalido: {error}"
        ) from error

    return parse_evaluation_dataset(payload)


__all__ = [
    "DATASET_SCHEMA_VERSION",
    "EXPECTED_QUESTION_COUNT",
    "GROUND_TRUTH_STATUS",
    "SIMPLE_QUESTION_COUNT",
    "TRAP_QUESTION_COUNT",
    "Category",
    "EvaluationDataset",
    "EvaluationDatasetError",
    "EvaluationQuestion",
    "load_evaluation_dataset",
    "parse_evaluation_dataset",
]
