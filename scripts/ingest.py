from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ecocidadao.config import get_settings
from ecocidadao.ingestion import (
    FIXED_CHUNK_OVERLAP,
    FIXED_CHUNK_SIZE,
    MARKDOWN_CHUNK_OVERLAP,
    MARKDOWN_CHUNK_SIZE,
    Chunk,
    Document,
    DocumentValidationError,
    chunk_documents,
    load_documents,
    validate_expected_documents,
)


def _write_jsonl(chunks: list[Chunk], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as file:
        for chunk in chunks:
            file.write(
                json.dumps(chunk.to_dict(), ensure_ascii=False) + "\n"
            )


def _length_statistics(chunks: list[Chunk]) -> dict[str, float | int]:
    lengths = [len(chunk.text) for chunk in chunks]
    if not lengths:
        return {"min": 0, "max": 0, "mean": 0.0, "median": 0.0}

    return {
        "min": min(lengths),
        "max": max(lengths),
        "mean": round(statistics.mean(lengths), 2),
        "median": statistics.median(lengths),
    }


def _strategy_summary(
    documents: list[Document],
    chunks: list[Chunk],
    strategy: str,
    chunk_size: int,
    chunk_overlap: int,
    output_file: Path,
) -> dict[str, Any]:
    counts_by_document = Counter(chunk.doc_id for chunk in chunks)

    return {
        "strategy": strategy,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "document_count": len(documents),
        "chunk_count": len(chunks),
        "char_length": _length_statistics(chunks),
        "output_file": output_file.name,
        "documents": [
            {
                **document.summary(),
                "chunk_count": counts_by_document[document.doc_id],
            }
            for document in documents
        ],
    }


def _write_summary(summary: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    settings = get_settings()

    parser = argparse.ArgumentParser(
        description="Executa a ingestao documental do EcoCidadao.",
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=settings.base_docs_dir,
        help="Diretorio dos documentos Markdown.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "chunks",
        help="Diretorio de saida dos chunks.",
    )
    parser.add_argument(
        "--strategy",
        choices=("ambas", "fixo", "markdown"),
        default="ambas",
        help="Estrategia de chunking a executar.",
    )
    args = parser.parse_args()

    try:
        documents = load_documents(args.docs_dir)
        validate_expected_documents(documents)
    except (DocumentValidationError, FileNotFoundError) as error:
        print(f"Erro de validacao: {error}", file=sys.stderr)
        return 1

    strategies = (
        ("fixo", "markdown")
        if args.strategy == "ambas"
        else (args.strategy,)
    )
    configuration = {
        "fixo": (FIXED_CHUNK_SIZE, FIXED_CHUNK_OVERLAP),
        "markdown": (MARKDOWN_CHUNK_SIZE, MARKDOWN_CHUNK_OVERLAP),
    }

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    strategy_summaries: list[dict[str, Any]] = []

    print(f"Documentos carregados: {len(documents)}")
    for document in documents:
        print(
            f"  - {document.doc_id}: {document.titulo} "
            f"({document.data_publicacao}, {document.word_count} palavras)"
        )

    for strategy in strategies:
        chunk_size, chunk_overlap = configuration[strategy]
        chunks = chunk_documents(documents, strategy)
        output_file = output_dir / f"chunks_{strategy}.jsonl"
        _write_jsonl(chunks, output_file)

        summary = _strategy_summary(
            documents=documents,
            chunks=chunks,
            strategy=strategy,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            output_file=output_file,
        )
        strategy_summaries.append(summary)
        statistics_data = summary["char_length"]
        print(
            f"[{strategy}] {len(chunks)} chunks | "
            f"tamanho min/med/max: "
            f"{statistics_data['min']}/{statistics_data['median']}/"
            f"{statistics_data['max']} | {output_file}"
        )

    summary_path = output_dir / "summary.json"
    _write_summary(
        {
            "schema_version": 1,
            "document_count": len(documents),
            "strategies": strategy_summaries,
        },
        summary_path,
    )
    print(f"Resumo: {summary_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
