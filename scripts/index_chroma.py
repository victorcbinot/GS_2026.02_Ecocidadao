from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ecocidadao.config import get_settings
from ecocidadao.ingestion import (
    DocumentValidationError,
    chunk_documents,
    load_documents,
    validate_expected_documents,
)
from ecocidadao.rag import (
    COLLECTION_BY_STRATEGY,
    ChromaVectorStore,
    LocalEmbeddingModel,
)


def main() -> int:
    settings = get_settings()

    parser = argparse.ArgumentParser(
        description=(
            "Gera embeddings locais e indexa os chunks no ChromaDB."
        ),
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=settings.base_docs_dir,
        help="Diretorio dos documentos Markdown.",
    )
    parser.add_argument(
        "--chroma-dir",
        type=Path,
        default=settings.chroma_dir,
        help="Diretorio de persistencia do ChromaDB.",
    )
    parser.add_argument(
        "--strategy",
        choices=("ambas", "fixo", "markdown"),
        default="ambas",
        help="Estrategia de chunking a indexar.",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Recria as colecoes antes de indexar.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Tamanho do lote de embeddings e de escrita.",
    )
    args = parser.parse_args()

    if args.batch_size < 1:
        print("Erro: --batch-size deve ser positivo.", file=sys.stderr)
        return 1

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

    print(f"Documentos carregados: {len(documents)}")
    print(f"Modelo de embeddings local: {settings.embedding_model}")
    print(f"Dispositivo: {settings.embedding_device}")
    print(f"Persistencia Chroma: {args.chroma_dir}")

    embedding_model = LocalEmbeddingModel(
        model_name=settings.embedding_model,
        device=settings.embedding_device,
        cache_dir=settings.hf_home,
        batch_size=args.batch_size,
    )

    for strategy in strategies:
        collection_name = COLLECTION_BY_STRATEGY[strategy]
        chunks = chunk_documents(documents, strategy)
        store = ChromaVectorStore(
            collection_name=collection_name,
            chroma_dir=args.chroma_dir,
            embedding_model=embedding_model,
            batch_size=args.batch_size,
        )
        result = store.create_or_update(
            chunks,
            replace_existing=args.recreate,
        )
        print(
            f"[{strategy}] colecao={result.collection_name} | "
            f"indexados={result.indexed} | removidos={result.deleted} | "
            f"total={result.total}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
