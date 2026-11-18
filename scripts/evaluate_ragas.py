from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ecocidadao.config import Settings, get_settings
from ecocidadao.evaluation import (
    RAGAS_METRIC_NAMES,
    EvaluationDataset,
    EvaluationDatasetError,
    build_ragas_result,
    load_evaluation_dataset,
    make_question_result,
)
from ecocidadao.rag import (
    RagResponse,
    RagService,
    create_judge_chat_model,
)


def _contexts_from_retrieved(retrieved: list[Any]) -> tuple[list[str], list[dict]]:
    contexts = [chunk.text for chunk in retrieved]
    metadata = [
        {
            "chunk_id": chunk.chunk_id,
            "doc_id": chunk.metadata.get("doc_id"),
            "source_file": chunk.metadata.get("source_file"),
            "section": chunk.metadata.get("section_path_text"),
            "similarity": chunk.similarity,
        }
        for chunk in retrieved
    ]
    return contexts, metadata


def _retrieve_all_contexts(
    service: RagService,
    dataset: EvaluationDataset,
    top_k: int,
) -> tuple[dict[str, list[str]], dict[str, list[dict]]]:
    contexts: dict[str, list[str]] = {}
    metadata: dict[str, list[dict]] = {}
    for question in dataset.questions:
        try:
            retrieved = service.retrieve(question.question, top_k=top_k)
            contexts[question.id], metadata[question.id] = (
                _contexts_from_retrieved(retrieved)
            )
        except Exception as error:
            contexts[question.id] = []
            metadata[question.id] = [
                {"retrieval_error": f"{type(error).__name__}: {error}"}
            ]
    return contexts, metadata


def _generate_all_answers(
    service: RagService,
    dataset: EvaluationDataset,
    top_k: int,
) -> tuple[dict[str, RagResponse], str | None]:
    responses: dict[str, RagResponse] = {}
    for question in dataset.questions:
        try:
            responses[question.id] = service.ask(
                question.question,
                top_k=top_k,
                as_of=question.as_of,
            )
        except Exception as error:
            return (
                responses,
                "A geracao real das respostas falhou; a avaliacao RAGAS "
                "nao foi executada. "
                f"Erro em {question.id}: {type(error).__name__}: {error}",
            )
    return responses, None


def _ragas_records(
    dataset: EvaluationDataset,
    responses: dict[str, RagResponse],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for question in dataset.questions:
        response = responses[question.id]
        records.append(
            {
                "user_input": question.question,
                "response": response.answer,
                "retrieved_contexts": [
                    source.text for source in response.sources
                ],
                "reference": question.ground_truth,
            }
        )
    return records


class _RagasEmbeddingAdapter:
    """Adapta o modelo local ao rastreamento do RAGAS.

    O wrapper do RAGAS usa o atributo ``model`` como nome textual. O
    LocalEmbeddingModel expõe ali o objeto SentenceTransformer, por isso
    este adaptador mantém o nome do modelo e delega apenas os embeddings.
    """

    def __init__(self, embedding_model: Any, model_name: str) -> None:
        self._embedding_model = embedding_model
        self.model = model_name

    def embed_query(self, text: str) -> list[float]:
        return self._embedding_model.embed_query(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embedding_model.embed_documents(texts)

    async def aembed_query(self, text: str) -> list[float]:
        return await self._embedding_model.aembed_query(text)

    async def aembed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        return await self._embedding_model.aembed_documents(texts)


def _run_ragas(
    records: list[dict[str, Any]],
    settings: Settings,
    embedding_model: Any,
) -> list[dict[str, Any]]:
    from ragas import EvaluationDataset, evaluate
    from ragas.embeddings.base import LangchainEmbeddingsWrapper
    from ragas.llms.base import LangchainLLMWrapper
    from ragas.metrics import (
        answer_relevancy,
        context_precision,
        context_recall,
        faithfulness,
    )
    from ragas.run_config import RunConfig

    llm = create_judge_chat_model(settings)
    wrapped_llm = LangchainLLMWrapper(llm, bypass_temperature=True)
    wrapped_embeddings = LangchainEmbeddingsWrapper(
        _RagasEmbeddingAdapter(
            embedding_model,
            settings.embedding_model,
        )
    )
    metrics = [
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    ]

    evaluation_dataset = EvaluationDataset.from_list(records)
    result = evaluate(
        evaluation_dataset,
        metrics=metrics,
        llm=wrapped_llm,
        embeddings=wrapped_embeddings,
        run_config=RunConfig(
            timeout=600,
            max_retries=3,
            max_wait=15,
            max_workers=1,
        ),
        batch_size=1,
        show_progress=True,
        raise_exceptions=False,
    )
    frame = result.to_pandas()
    return [
        {
            name: row.get(name)
            for name in RAGAS_METRIC_NAMES
        }
        for row in frame.to_dict(orient="records")
    ]


def _configuration(
    settings: Settings,
    dataset_path: Path,
    collection_name: str,
    top_k: int,
) -> dict[str, Any]:
    return {
        "collection_name": collection_name,
        "top_k": top_k,
        "llm_model": settings.ollama_model or None,
        "llm_base_url": settings.ollama_base_url,
        "ragas_judge_model": settings.ragas_judge_model or None,
        "ragas_judge_base_url": settings.ragas_judge_base_url,
        "ragas_judge_execution": (
            "local_ollama"
            if settings.uses_local_ragas_judge
            else "remote_ollama"
        ),
        "embedding_model": settings.embedding_model,
        "embedding_execution": "local_sentence_transformers",
        "dataset_path": str(dataset_path),
        "ragas_version": _ragas_version(),
    }


def _ragas_version() -> str | None:
    try:
        import ragas

        return getattr(ragas, "__version__", None)
    except ImportError:
        return None


def _write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _question_results(
    dataset: EvaluationDataset,
    *,
    responses: dict[str, RagResponse],
    contexts: dict[str, list[str]],
    context_metadata: dict[str, list[dict]],
    metrics_by_index: list[dict[str, Any]] | None,
    status: str,
    error: str | None,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for index, question in enumerate(dataset.questions):
        response = responses.get(question.id)
        if response is not None:
            response_contexts = [
                source.text for source in response.sources
            ]
            response_metadata = [
                {
                    "chunk_id": source.chunk_id,
                    "doc_id": source.doc_id,
                    "source_file": source.source_file,
                    "section": source.section,
                    "similarity": source.similarity,
                }
                for source in response.sources
            ]
        else:
            response_contexts = contexts.get(question.id, [])
            response_metadata = context_metadata.get(question.id, [])

        metrics = (
            metrics_by_index[index]
            if metrics_by_index is not None
            and index < len(metrics_by_index)
            else None
        )
        question_status = (
            "executado"
            if status == "executado" and response is not None
            else status
        )
        results.append(
            make_question_result(
                question,
                generated_answer=(
                    response.answer if response is not None else None
                ),
                contexts=response_contexts,
                context_metadata=response_metadata,
                metrics=metrics,
                status=question_status,
                error=error,
            )
        )
    return results


def main() -> int:
    settings = get_settings()

    parser = argparse.ArgumentParser(
        description=(
            "Executa a avaliacao RAGAS real do EcoCidadao com oito perguntas."
        ),
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=settings.evaluation_dataset_path,
        help="Dataset com as oito perguntas e ground truths.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=settings.ragas_output_path,
        help="Arquivo JSON de saida da avaliacao.",
    )
    parser.add_argument(
        "--collection",
        default=settings.collection_name,
        help="Colecao ChromaDB usada na recuperacao.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=settings.retrieval_top_k,
        help="Quantidade de trechos recuperados.",
    )
    args = parser.parse_args()

    if args.top_k < 1:
        print("Erro: --top-k deve ser positivo.", file=sys.stderr)
        return 1

    try:
        dataset = load_evaluation_dataset(args.dataset)
    except (EvaluationDatasetError, FileNotFoundError) as error:
        print(f"Erro no dataset: {error}", file=sys.stderr)
        return 1

    service = RagService(collection_name=args.collection)
    contexts, context_metadata = _retrieve_all_contexts(
        service,
        dataset,
        args.top_k,
    )
    responses, generation_error = _generate_all_answers(
        service,
        dataset,
        args.top_k,
    )

    metrics_by_index: list[dict[str, Any]] | None = None
    status = "pendente"
    reason = generation_error

    if generation_error is None:
        embedding_model = service.embedding_model
        if embedding_model is None:
            from ecocidadao.rag import LocalEmbeddingModel

            embedding_model = LocalEmbeddingModel(
                model_name=settings.embedding_model,
                device=settings.embedding_device,
                cache_dir=settings.hf_home,
            )
        try:
            metrics_by_index = _run_ragas(
                _ragas_records(dataset, responses),
                settings,
                embedding_model,
            )
            status = "executado"
            reason = None
        except Exception as error:
            status = "pendente"
            reason = (
                "As respostas foram geradas, mas a avaliacao RAGAS falhou. "
                f"Erro: {type(error).__name__}: {error}"
            )

    question_results = _question_results(
        dataset,
        responses=responses,
        contexts=contexts,
        context_metadata=context_metadata,
        metrics_by_index=metrics_by_index,
        status=status,
        error=reason,
    )
    payload = build_ragas_result(
        dataset=dataset,
        dataset_path=args.dataset,
        status=status,
        reason=reason,
        configuration=_configuration(
            settings,
            args.dataset,
            args.collection,
            args.top_k,
        ),
        question_results=question_results,
    )
    _write_json(payload, args.output)

    print(f"Perguntas: {len(dataset.questions)}")
    print(f"Saida: {args.output}")
    print(f"Status: {payload['status']}")
    if payload["reason"]:
        print(f"Motivo: {payload['reason']}")
    if status == "executado":
        for name, value in payload["summary"].items():
            print(f"{name}: {value}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
