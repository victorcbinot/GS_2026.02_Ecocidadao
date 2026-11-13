from __future__ import annotations

from datetime import date
from typing import Callable

from langchain_core.tools import BaseTool, tool

from ..rag import RagResponse, RagService
from .calculator import CalculationError, calculate, format_number
from .ecopontos import EcopontoCatalog, EcopontoDataError, EcopontoStatus


def _format_documents(response: RagResponse) -> str:
    lines = [
        "Resposta documental (já validada pelos guardrails):",
        response.answer,
        "",
        f"Data de referência: {response.as_of}",
        "Fontes documentais:",
    ]
    sources = response.cited_sources or response.sources
    if sources:
        lines.extend(f"- {source.citation()}" for source in sources)
    else:
        lines.append("- nenhuma fonte documental recuperada")

    lines.extend(
        [
            "",
            "Contexto documental recuperado:",
            response.context or "nenhum trecho disponível",
        ]
    )
    if response.guardrail_events:
        lines.append("")
        lines.append(
            "Eventos de guardrail: "
            + ", ".join(response.guardrail_events)
        )
    if response.blocked_by_guardrail:
        lines.append(
            "A resposta documental foi bloqueada ou limitada por guardrail."
        )
    return "\n".join(lines)


def _format_status(status: EcopontoStatus, detailed: bool) -> str:
    lines = [
        f"- {status.ecoponto.nome}: {status.situacao}",
        f"  Endereço: {status.ecoponto.endereco}",
        f"  Horário: {status.horario}",
    ]
    if detailed:
        lines.append(
            "  Materiais aceitos: "
            + (
                ", ".join(status.materiais_aceitos)
                if status.materiais_aceitos
                else "nenhum no período"
            )
        )
        lines.append(
            "  Materiais não aceitos: "
            + (
                ", ".join(status.materiais_nao_aceitos)
                if status.materiais_nao_aceitos
                else "não informado"
            )
        )
    if status.material_consultado:
        verdict = "aceito" if status.aceita_material else "não aceito"
        lines.append(
            f"  Material consultado ({status.material_consultado}): {verdict}"
        )
    if status.alternativas:
        lines.append(
            "  Alternativa(s): " + "; ".join(status.alternativas)
        )
    if status.aviso:
        lines.append(f"  Aviso: {status.aviso}")
    return "\n".join(lines)


def _format_ecopontos(
    statuses: list[EcopontoStatus],
    material: str,
    as_of: str,
    accepted: list[EcopontoStatus],
    rejected: list[EcopontoStatus],
    observacoes: tuple[str, ...],
) -> str:
    lines = [
        f"Consulta aos Ecopontos de EcoCidade em {as_of}.",
        "Fonte estruturada: data/ecopontos.json, coerente com a Lista de "
        "Ecopontos de 2026-02-01 e o Comunicado de Interdição de "
        "2026-03-10. Estes dados não são uma citação documental [F].",
    ]
    if material:
        lines.extend(
            [
                "",
                f"Materiais consultados: {material}.",
                "Ecopontos que aceitam:",
            ]
        )
        if accepted:
            lines.extend(
                _format_status(status, detailed=True)
                for status in accepted
            )
        else:
            lines.append("- nenhum")
        lines.append("Ecopontos que não aceitam:")
        if rejected:
            lines.extend(
                _format_status(status, detailed=False)
                for status in rejected
            )
        else:
            lines.append("- nenhum")
        if rejected and not accepted:
            lines.append(
                "Nenhum Ecoponto aceita esse material na data consultada; "
                "verifique as alternativas indicadas."
            )
    else:
        lines.extend(
            _format_status(status, detailed=True) for status in statuses
        )
    if observacoes:
        lines.extend(["", "Observações gerais:"])
        lines.extend(f"- {item}" for item in observacoes)
    return "\n".join(lines)


def build_tools(
    rag_service: RagService,
    ecopontos: EcopontoCatalog,
    now_provider: Callable[[], date] | None = None,
) -> list[BaseTool]:
    current_date = now_provider or date.today

    @tool("consultar_base_documental")
    def consultar_base_documental(
        pergunta: str,
        data_referencia: str = "",
    ) -> str:
        """Consulta a base documental com RAG e guardrails.

        Use para regras, materiais, limites, medicamentos, interdições e
        qualquer informação que precise de citação documental. Retorna a
        resposta, o contexto e as fontes com os rótulos [F1], [F2] etc.
        """
        if not pergunta or not pergunta.strip():
            return "Erro controlado: a pergunta documental não pode ser vazia."
        try:
            response = rag_service.ask(
                pergunta,
                as_of=data_referencia.strip() or None,
            )
        except Exception as error:
            return (
                "Erro controlado na consulta documental: "
                f"{error}. Não invente uma resposta."
            )
        return _format_documents(response)

    @tool("consultar_ecopontos")
    def consultar_ecopontos(
        ecoponto: str = "",
        material: str = "",
        data_referencia: str = "",
    ) -> str:
        """Consulta endereço, horário, materiais e situação dos Ecopontos.

        Informe opcionalmente o nome do Ecoponto, o material desejado e a
        data de referência ISO AAAA-MM-DD. A função considera a interdição
        do Parque das Acácias e as mudanças válidas a partir de 2026-06-01.
        """
        try:
            as_of = (
                date.fromisoformat(data_referencia.strip())
                if data_referencia.strip()
                else current_date()
            )
            statuses = ecopontos.query(
                nome=ecoponto.strip() or None,
                material=material.strip() or None,
                as_of=as_of,
            )
        except (ValueError, EcopontoDataError) as error:
            return f"Erro controlado na consulta aos Ecopontos: {error}"

        if not statuses:
            return (
                "Nenhum Ecoponto encontrado para os critérios informados."
            )

        all_statuses = (
            ecopontos.query(material=material.strip(), as_of=as_of)
            if material.strip()
            else statuses
        )
        accepted = [
            status
            for status in all_statuses
            if status.aceita_material is True
        ]
        rejected = [
            status for status in statuses if status.aceita_material is False
        ]
        return _format_ecopontos(
            statuses=statuses,
            material=material.strip(),
            as_of=as_of.isoformat(),
            accepted=accepted,
            rejected=rejected,
            observacoes=ecopontos.observacoes,
        )

    @tool("calcular")
    def calcular(expressao: str) -> str:
        """Calcula quantidade, peso, volume, proporção ou estimativa.

        Aceita apenas números, operadores matemáticos e funções seguras
        como round, min, max, abs, sqrt, ceil e floor. Não execute código
        arbitrário. O resultado é uma estimativa calculada, não um dado
        oficial da Prefeitura.
        """
        try:
            result = calculate(expressao)
        except CalculationError as error:
            return f"Erro controlado na calculadora: {error}"
        return (
            f"Resultado do cálculo: {format_number(result)}. "
            "Este é um resultado calculado/estimado, não um dado oficial."
        )

    @tool("data_atual")
    def data_atual() -> str:
        """Retorna a data atual no formato ISO AAAA-MM-DD.

        Use para interpretar corretamente interdições, reaberturas e
        mudanças com validade temporal.
        """
        return f"Data atual: {current_date().isoformat()}"

    return [
        consultar_base_documental,
        consultar_ecopontos,
        calcular,
        data_atual,
    ]


__all__ = ["build_tools"]
