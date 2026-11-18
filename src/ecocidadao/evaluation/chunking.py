from __future__ import annotations

import shutil
import statistics
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from ..ingestion import (
    FIXED_CHUNK_OVERLAP,
    FIXED_CHUNK_SIZE,
    MARKDOWN_CHUNK_OVERLAP,
    MARKDOWN_CHUNK_SIZE,
    Chunk,
    Document,
    chunk_documents,
)
from ..rag import (
    COLLECTION_BY_STRATEGY,
    ChromaVectorStore,
    EmbeddingModel,
)
from .dataset import EvaluationDataset, EvaluationQuestion
from .results import utc_timestamp

EXPERIMENT_SCHEMA_VERSION = 1
EXPERIMENT_STATUS = "parcialmente_executado"
RAGAS_CONTEXT_STATUS = "pendente"
RAGAS_CONTEXT_REASON = (
    "As metricas RAGAS context_precision e context_recall dependem de um "
    "modelo de linguagem. A comparacao de chunking mediu apenas o retrieval; "
    "as metricas RAGAS permanecem pendentes."
)
WINNER_REASON = (
    "Nenhuma estrategia foi declarada vencedora: o retrieval foi medido, mas "
    "as metricas RAGAS de contexto e a validacao humana dos ground truths "
    "ainda estao pendentes."
)
RECOMMENDED_STRATEGY = "markdown"
RECOMMENDATION_REASON = (
    "Recomendacao tecnica baseada nos dados de retrieval: as duas estrategias "
    "empatam em Hit@3, Hit@5 e MRR; a Markdown tem precision documental maior "
    "(0.80 contra 0.725), chunks menores e preserva a hierarquia de secoes. "
    "O recall documental e menor (0.875 contra 1.0) em duas armadilhas, o que "
    "deve ser monitorado com a janela temporal ampliada. Nao e um vencedor "
    "estatistico definitivo sem RAGAS por estrategia."
)
_STRATEGY_CONFIG = {
    "fixo": {
        "chunk_size": FIXED_CHUNK_SIZE,
        "chunk_overlap": FIXED_CHUNK_OVERLAP,
    },
    "markdown": {
        "chunk_size": MARKDOWN_CHUNK_SIZE,
        "chunk_overlap": MARKDOWN_CHUNK_OVERLAP,
    },
}


class ChunkingExperimentError(ValueError):
    pass


def length_statistics(values: Iterable[int]) -> dict[str, float | int]:
    items = [int(value) for value in values]
    if not items:
        return {"min": 0, "max": 0, "mean": 0.0, "median": 0.0}
    return {
        "min": min(items),
        "max": max(items),
        "mean": round(statistics.mean(items), 2),
        "median": statistics.median(items),
    }


def compute_ranking_metrics(
    ranked_doc_ids: Sequence[str],
    relevant_doc_ids: Iterable[str],
    k_values: Sequence[int] = (3, 5),
) -> dict[str, Any]:
    relevant = {str(doc_id) for doc_id in relevant_doc_ids}
    if not relevant:
        raise ChunkingExperimentError(
            "A lista de documentos relevantes nao pode ser vazia."
        )

    metrics: dict[str, Any] = {}
    for k in k_values:
        if k < 1:
            raise ChunkingExperimentError(
                "Os valores de k devem ser positivos."
            )
        metrics[f"hit_at_{k}"] = any(
            str(doc_id) in relevant for doc_id in ranked_doc_ids[:k]
        )

    first_relevant_rank: int | None = None
    for index, doc_id in enumerate(ranked_doc_ids, start=1):
        if str(doc_id) in relevant:
            first_relevant_rank = index
            break

    metrics["first_relevant_rank"] = first_relevant_rank
    metrics["mrr"] = (
        1.0 / first_relevant_rank if first_relevant_rank else 0.0
    )
    metrics["relevant_retrieved"] = sorted(
        {str(doc_id) for doc_id in ranked_doc_ids} & relevant
    )
    metrics["missing_relevant"] = sorted(
        relevant - {str(doc_id) for doc_id in ranked_doc_ids}
    )
    return metrics


def _document_precision(
    ranked_doc_ids: Sequence[str],
    relevant_doc_ids: Iterable[str],
) -> float | None:
    if not ranked_doc_ids:
        return None
    relevant = {str(doc_id) for doc_id in relevant_doc_ids}
    relevant_count = sum(
        str(doc_id) in relevant for doc_id in ranked_doc_ids
    )
    return round(relevant_count / len(ranked_doc_ids), 6)


def _document_recall(
    ranked_doc_ids: Sequence[str],
    relevant_doc_ids: Iterable[str],
) -> float | None:
    relevant = {str(doc_id) for doc_id in relevant_doc_ids}
    if not relevant:
        return None
    retrieved = {str(doc_id) for doc_id in ranked_doc_ids}
    return round(len(retrieved & relevant) / len(relevant), 6)


def _mean(values: Iterable[Any]) -> float | None:
    numbers = [
        float(value)
        for value in values
        if isinstance(value, (int, float, bool))
    ]
    if not numbers:
        return None
    return round(statistics.mean(numbers), 6)


def _question_result(
    question: EvaluationQuestion,
    retrieved: list[Any],
) -> dict[str, Any]:
    ranked_doc_ids = [
        str(item.metadata.get("doc_id") or "documento")
        for item in retrieved
    ]
    ranking = compute_ranking_metrics(
        ranked_doc_ids=ranked_doc_ids,
        relevant_doc_ids=question.reference_doc_ids,
        k_values=(3, 5),
    )
    ranking["context_document_precision"] = _document_precision(
        ranked_doc_ids,
        question.reference_doc_ids,
    )
    ranking["context_document_recall"] = _document_recall(
        ranked_doc_ids,
        question.reference_doc_ids,
    )

    return {
        "id": question.id,
        "category": question.category,
        "question": question.question,
        "as_of": question.as_of,
        "relevant_doc_ids": list(question.reference_doc_ids),
        "retrieved": [
            {
                "rank": rank,
                "chunk_id": item.chunk_id,
                "doc_id": str(item.metadata.get("doc_id") or "documento"),
                "similarity": round(float(item.similarity), 6),
                "text_preview": item.text[:240],
            }
            for rank, item in enumerate(retrieved, start=1)
        ],
        "ranking": ranking,
        "ragas_context_precision": None,
        "ragas_context_recall": None,
        "ragas_status": RAGAS_CONTEXT_STATUS,
    }


def _chunk_statistics(chunks: list[Chunk]) -> dict[str, Any]:
    return {
        "chunk_count": len(chunks),
        "char_length": length_statistics(
            len(chunk.text) for chunk in chunks
        ),
        "word_length": length_statistics(
            len(chunk.text.split()) for chunk in chunks
        ),
    }


def _strategy_result(
    *,
    strategy: str,
    chunks: list[Chunk],
    questions: Sequence[EvaluationQuestion],
    embedding_model: EmbeddingModel,
    chroma_dir: Path,
    top_k: int,
    batch_size: int,
) -> dict[str, Any]:
    collection_name = COLLECTION_BY_STRATEGY[strategy]
    store = ChromaVectorStore(
        collection_name=collection_name,
        chroma_dir=chroma_dir,
        embedding_model=embedding_model,
        batch_size=batch_size,
    )
    index_result = store.create_or_update(
        chunks,
        replace_existing=True,
    )

    question_results: list[dict[str, Any]] = []
    for question in questions:
        retrieved = store.query(question.question, top_k=top_k)
        question_results.append(_question_result(question, retrieved))

    return {
        "strategy": strategy,
        "collection_name": collection_name,
        "configuration": dict(_STRATEGY_CONFIG[strategy]),
        **_chunk_statistics(chunks),
        "indexed": index_result.indexed,
        "retrieval": {
            "top_k": top_k,
            "score_threshold": None,
            "metrics": {
                "mean_hit_at_3": _mean(
                    item["ranking"]["hit_at_3"]
                    for item in question_results
                ),
                "mean_hit_at_5": _mean(
                    item["ranking"]["hit_at_5"]
                    for item in question_results
                ),
                "mean_mrr": _mean(
                    item["ranking"]["mrr"]
                    for item in question_results
                ),
                "mean_context_document_precision": _mean(
                    item["ranking"]["context_document_precision"]
                    for item in question_results
                ),
                "mean_context_document_recall": _mean(
                    item["ranking"]["context_document_recall"]
                    for item in question_results
                ),
            },
            "ragas_context_precision": None,
            "ragas_context_recall": None,
            "ragas_status": RAGAS_CONTEXT_STATUS,
            "ragas_reason": RAGAS_CONTEXT_REASON,
            "questions": question_results,
        },
    }


def build_chunking_experiment(
    *,
    documents: Sequence[Document],
    dataset: EvaluationDataset,
    dataset_path: Path | str,
    embedding_model: EmbeddingModel,
    top_k: int = 5,
    batch_size: int = 32,
    generated_at: str | None = None,
) -> dict[str, Any]:
    if top_k < 5:
        raise ChunkingExperimentError(
            "top_k deve ser pelo menos 5 para calcular Hit@5."
        )
    if len(documents) != 3:
        raise ChunkingExperimentError(
            "A comparacao exige os tres documentos da base."
        )

    temporary_dir = Path(
        tempfile.mkdtemp(prefix="ecocidadao-chunking-experiment-")
    )
    try:
        strategy_results: list[dict[str, Any]] = []
        for strategy in ("fixo", "markdown"):
            chunks = chunk_documents(list(documents), strategy)
            strategy_results.append(
                _strategy_result(
                    strategy=strategy,
                    chunks=chunks,
                    questions=dataset.questions,
                    embedding_model=embedding_model,
                    chroma_dir=temporary_dir,
                    top_k=top_k,
                    batch_size=batch_size,
                )
            )
    finally:
        shutil.rmtree(temporary_dir, ignore_errors=True)

    payload = {
        "schema_version": EXPERIMENT_SCHEMA_VERSION,
        "status": EXPERIMENT_STATUS,
        "generated_at": generated_at or utc_timestamp(),
        "dataset": {
            "source": str(dataset_path),
            "question_count": len(dataset.questions),
            "simple_question_count": dataset.simple_count,
            "trap_question_count": dataset.trap_count,
            "ground_truth_status": dataset.ground_truth_status,
        },
        "configuration": {
            "top_k": top_k,
            "batch_size": batch_size,
            "chroma_mode": "temporario",
            "embedding_model": getattr(
                embedding_model,
                "model_name",
                type(embedding_model).__name__,
            ),
            "strategies": {
                strategy: dict(config)
                for strategy, config in _STRATEGY_CONFIG.items()
            },
        },
        "winner": None,
        "winner_reason": WINNER_REASON,
        "recommended_strategy": RECOMMENDED_STRATEGY,
        "recommendation_reason": RECOMMENDATION_REASON,
        "ragas_status": RAGAS_CONTEXT_STATUS,
        "ragas_reason": RAGAS_CONTEXT_REASON,
        "strategies": strategy_results,
    }
    validate_chunking_experiment(payload)
    return payload


def validate_chunking_experiment(payload: Any) -> None:
    if not isinstance(payload, dict):
        raise ChunkingExperimentError(
            "O experimento de chunking deve ser um objeto JSON."
        )
    if payload.get("schema_version") != EXPERIMENT_SCHEMA_VERSION:
        raise ChunkingExperimentError(
            "Versao de schema do experimento invalida."
        )
    if payload.get("status") != EXPERIMENT_STATUS:
        raise ChunkingExperimentError(
            "Status inesperado no experimento de chunking."
        )
    if payload.get("winner") is not None:
        raise ChunkingExperimentError(
            "Nenhuma estrategia pode ser declarada vencedora sem as "
            "metricas RAGAS e a validacao dos ground truths."
        )

    dataset = payload.get("dataset")
    if not isinstance(dataset, dict):
        raise ChunkingExperimentError("Campo 'dataset' invalido.")
    if dataset.get("question_count") != len(
        payload.get("strategies", [{}])[0].get("retrieval", {}).get(
            "questions",
            [],
        )
    ):
        raise ChunkingExperimentError(
            "A quantidade de perguntas do experimento e inconsistente."
        )

    strategies = payload.get("strategies")
    if not isinstance(strategies, list) or len(strategies) != 2:
        raise ChunkingExperimentError(
            "O experimento deve comparar exatamente duas estrategias."
        )
    names = {item.get("strategy") for item in strategies if isinstance(item, dict)}
    if names != {"fixo", "markdown"}:
        raise ChunkingExperimentError(
            "As estrategias do experimento devem ser 'fixo' e 'markdown'."
        )

    for strategy in strategies:
        if not isinstance(strategy, dict):
            raise ChunkingExperimentError("Estrategia invalida.")
        if strategy.get("chunk_count", 0) < 1:
            raise ChunkingExperimentError(
                "Cada estrategia deve ter pelo menos um chunk."
            )
        retrieval = strategy.get("retrieval")
        if not isinstance(retrieval, dict):
            raise ChunkingExperimentError(
                "Campo 'retrieval' invalido no experimento."
            )
        metrics = retrieval.get("metrics")
        if not isinstance(metrics, dict):
            raise ChunkingExperimentError(
                "Metricas de retrieval invalidas no experimento."
            )
        for key in (
            "mean_hit_at_3",
            "mean_hit_at_5",
            "mean_mrr",
            "mean_context_document_precision",
            "mean_context_document_recall",
        ):
            if key not in metrics:
                raise ChunkingExperimentError(
                    f"Metrica ausente no experimento: {key}."
                )
        if not isinstance(retrieval.get("questions"), list):
            raise ChunkingExperimentError(
                "Lista de perguntas do retrieval invalida."
            )


__all__ = [
    "EXPERIMENT_SCHEMA_VERSION",
    "EXPERIMENT_STATUS",
    "RECOMMENDED_STRATEGY",
    "RECOMMENDATION_REASON",
    "ChunkingExperimentError",
    "build_chunking_experiment",
    "compute_ranking_metrics",
    "length_statistics",
    "validate_chunking_experiment",
]
