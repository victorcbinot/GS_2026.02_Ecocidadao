from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ecocidadao.config import get_settings
from ecocidadao.rag import (
    COLLECTION_FIXO,
    COLLECTION_MARKDOWN,
    CollectionNotFoundError,
    LLMConfigurationError,
    RagService,
    RagServiceError,
)


def main() -> int:
    settings = get_settings()

    parser = argparse.ArgumentParser(
        description="Faz uma pergunta ao servico RAG do EcoCidadao.",
    )
    parser.add_argument(
        "question",
        help="Pergunta do cidadao.",
    )
    parser.add_argument(
        "--collection",
        choices=(COLLECTION_FIXO, COLLECTION_MARKDOWN),
        default=settings.collection_name,
        help="Colecao de chunks a consultar.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=settings.retrieval_top_k,
        help="Quantidade de trechos recuperados.",
    )
    parser.add_argument(
        "--as-of",
        default=None,
        help="Data de referencia no formato ISO AAAA-MM-DD.",
    )
    args = parser.parse_args()

    service = RagService(collection_name=args.collection)
    try:
        response = service.ask(
            question=args.question,
            collection_name=args.collection,
            top_k=args.top_k,
            as_of=args.as_of,
        )
    except (
        CollectionNotFoundError,
        LLMConfigurationError,
        RagServiceError,
        ValueError,
    ) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1

    print(response.answer)
    print()
    print(f"Colecao: {response.collection_name}")
    print(f"Data de referencia: {response.as_of}")
    print(f"Bloqueado por guardrail: {'sim' if response.blocked_by_guardrail else 'nao'}")
    if response.guardrail_events:
        print(f"Eventos de guardrail: {', '.join(response.guardrail_events)}")

    sources = response.cited_sources or response.sources
    if sources:
        print("Fontes:")
        for source in sources:
            print(f"  {source.citation()}")
    else:
        print("Fontes: nenhuma")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
