from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ecocidadao.config import get_settings
from ecocidadao.evaluation import (
    ChunkingExperimentError,
    EvaluationDatasetError,
    build_chunking_experiment,
    load_evaluation_dataset,
)
from ecocidadao.ingestion import (
    DocumentValidationError,
    load_documents,
    validate_expected_documents,
)
from ecocidadao.rag import LocalEmbeddingModel, VectorStoreError


def _write_json(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _format_number(value: object) -> str:
    if value is None:
        return "n/d"
    return f"{float(value):.4f}"


def main() -> int:
    settings = get_settings()

    parser = argparse.ArgumentParser(
        description=(
            "Compara as estrategias de chunking fixo e markdown usando "
            "retrieval medido no ChromaDB."
        ),
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=settings.base_docs_dir,
        help="Diretorio dos documentos Markdown.",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=settings.evaluation_dataset_path,
        help="Dataset com as perguntas e documentos relevantes.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=settings.chunking_experiment_path,
        help="Arquivo JSON de saida do experimento.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Quantidade de chunks recuperados por pergunta.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Tamanho dos lotes de embeddings e indexacao.",
    )
    args = parser.parse_args()

    if args.top_k < 5:
        print("Erro: --top-k deve ser pelo menos 5.", file=sys.stderr)
        return 1
    if args.batch_size < 1:
        print("Erro: --batch-size deve ser positivo.", file=sys.stderr)
        return 1

    try:
        documents = load_documents(args.docs_dir)
        validate_expected_documents(documents)
        dataset = load_evaluation_dataset(args.dataset)
    except (
        DocumentValidationError,
        EvaluationDatasetError,
        FileNotFoundError,
    ) as error:
        print(f"Erro de validacao: {error}", file=sys.stderr)
        return 1

    embedding_model = LocalEmbeddingModel(
        model_name=settings.embedding_model,
        device=settings.embedding_device,
        cache_dir=settings.hf_home,
        batch_size=args.batch_size,
    )

    try:
        payload = build_chunking_experiment(
            documents=documents,
            dataset=dataset,
            dataset_path=args.dataset,
            embedding_model=embedding_model,
            top_k=args.top_k,
            batch_size=args.batch_size,
        )
    except (
        ChunkingExperimentError,
        VectorStoreError,
        RuntimeError,
        OSError,
        ValueError,
    ) as error:
        print(f"Erro na comparacao de chunking: {error}", file=sys.stderr)
        return 1

    _write_json(payload, args.output)

    print(f"Documentos: {len(documents)}")
    print(f"Perguntas: {len(dataset.questions)}")
    print(f"Top-k: {args.top_k}")
    print(f"Saida: {args.output}")
    for strategy in payload["strategies"]:
        metrics = strategy["retrieval"]["metrics"]
        print(
            f"[{strategy['strategy']}] chunks={strategy['chunk_count']} | "
            f"media_chars={strategy['char_length']['mean']} | "
            f"Hit@3={_format_number(metrics['mean_hit_at_3'])} | "
            f"Hit@5={_format_number(metrics['mean_hit_at_5'])} | "
            f"MRR={_format_number(metrics['mean_mrr'])}"
        )
    print("Vencedor empirico: nao declarado")
    print(f"Recomendacao tecnica: {payload['recommended_strategy']}")
    print(f"RAGAS context precision/recall: {payload['ragas_status']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
