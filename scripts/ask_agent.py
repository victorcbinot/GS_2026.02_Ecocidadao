from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ecocidadao.agent import (
    AgentConfigurationError,
    EcopontoDataError,
    EcoCidadaoAgent,
)
from ecocidadao.config import get_settings
from ecocidadao.rag import (
    CollectionNotFoundError,
    LLMConfigurationError,
    RagServiceError,
)


def main() -> int:
    settings = get_settings()

    parser = argparse.ArgumentParser(
        description="Faz uma pergunta ao agente EcoCidadao.",
    )
    parser.add_argument("question", help="Pergunta do cidadao.")
    parser.add_argument(
        "--as-of",
        default=None,
        help="Data de referencia no formato ISO AAAA-MM-DD.",
    )
    parser.add_argument(
        "--max-tool-calls",
        type=int,
        default=settings.max_tool_calls,
        choices=range(1, settings.max_tool_calls + 1),
        metavar="1-6",
        help="Limite de chamadas de ferramentas (maximo 6).",
    )
    args = parser.parse_args()

    try:
        agent = EcoCidadaoAgent(
            max_tool_calls=args.max_tool_calls,
            settings=settings,
        )
        response = agent.ask(args.question, as_of=args.as_of)
    except (
        AgentConfigurationError,
        CollectionNotFoundError,
        EcopontoDataError,
        LLMConfigurationError,
        RagServiceError,
        ValueError,
    ) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1

    print(response.answer)
    print()
    print(f"Chamadas de ferramentas: {response.tool_call_count}")
    for call in response.tool_calls:
        status = "erro" if call.error else "ok"
        print(f"- {call.name} ({status}): {call.arguments}")
    if response.guardrail_events:
        print(
            "Eventos de guardrail: "
            + ", ".join(response.guardrail_events)
        )
    print(
        "Bloqueado por guardrail: "
        f"{'sim' if response.blocked_by_guardrail else 'nao'}"
    )
    print(f"Motivo de parada: {response.stopped_reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
