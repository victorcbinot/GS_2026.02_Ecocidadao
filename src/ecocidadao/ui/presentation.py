from __future__ import annotations

from ..agent import AGENT_ERROR_ANSWER, AgentResponse, ToolCallRecord

OLLAMA_UNAVAILABLE_ANSWER = (
    "Não foi possível conectar ao Ollama local. Verifique se o serviço do "
    "Ollama está em execução, se o modelo configurado foi baixado e se a "
    "URL local está correta, depois tente novamente."
)

VECTOR_STORE_UNAVAILABLE_ANSWER = (
    "Não foi possível acessar o banco vetorial ou a base documental. "
    "Verifique se a ingestão foi executada e se o banco local está "
    "disponível, depois tente novamente."
)

ECOPONTO_UNAVAILABLE_ANSWER = (
    "Não foi possível consultar a base estruturada dos Ecopontos. "
    "Verifique o arquivo data/ecopontos.json e tente novamente."
)

_LLM_ERROR_MARKERS = (
    "modelo de linguagem",
    "ollama",
    "402",
    "401",
    "unauthorized",
    "payment required",
    "connection refused",
    "connection error",
    "connect timeout",
    "timed out",
    "timeout",
    "falha ao consultar o modelo",
)
_VECTOR_ERROR_MARKERS = (
    "chroma",
    "banco vetorial",
    "coleção",
    "colecao",
    "collection",
    "embedding",
    "nothing found",
    "persist",
)


def _document_records(
    response: AgentResponse,
) -> tuple[ToolCallRecord, ...]:
    return tuple(
        call
        for call in response.tool_calls
        if call.name == "consultar_base_documental"
    )


def _has_document_tool(response: AgentResponse) -> bool:
    return bool(_document_records(response))


def _has_ecoponto_error(response: AgentResponse) -> bool:
    return any(
        call.name == "consultar_ecopontos" and call.error
        for call in response.tool_calls
    )


def _has_document_error(response: AgentResponse) -> bool:
    return any(call.error for call in _document_records(response))


def _is_llm_failure(response: AgentResponse) -> bool:
    if response.stopped_reason == "llm_error":
        return True
    for call in response.tool_calls:
        if not call.error:
            continue
        text = call.result.casefold()
        if any(marker in text for marker in _LLM_ERROR_MARKERS):
            return True
    return False


def _is_vector_store_failure(response: AgentResponse) -> bool:
    if not _has_document_error(response):
        return False
    for call in _document_records(response):
        if not call.error:
            continue
        text = call.result.casefold()
        if any(marker in text for marker in _VECTOR_ERROR_MARKERS):
            return True
    return not _is_llm_failure(response)


def status_title(response: AgentResponse) -> str:
    reason = response.stopped_reason
    if reason == "input_guardrail":
        return "Solicitação recusada pelos guardrails"
    if reason == "llm_error" or _is_llm_failure(response):
        return "Falha de conexão com o Ollama local"
    if _is_vector_store_failure(response):
        return "Base documental ou banco vetorial indisponível"
    if _has_ecoponto_error(response):
        return "Dados dos Ecopontos indisponíveis"
    if reason == "insufficient_context":
        return "Contexto insuficiente"
    if reason == "tool_call_limit":
        return "Limite de ferramentas atingido"
    if reason == "repeated_tool_call":
        return "Chamada repetida detectada"
    if reason == "output_guardrail":
        return "Resposta bloqueada por segurança"
    if response.blocked_by_guardrail:
        return "Resposta limitada por segurança"
    return "Resposta concluída"


def display_answer(response: AgentResponse) -> str:
    if response.stopped_reason == "llm_error":
        return OLLAMA_UNAVAILABLE_ANSWER
    if (
        response.blocked_by_guardrail
        and response.stopped_reason == "insufficient_context"
    ) or response.answer == AGENT_ERROR_ANSWER:
        if _is_llm_failure(response):
            return OLLAMA_UNAVAILABLE_ANSWER
        if _is_vector_store_failure(response):
            return VECTOR_STORE_UNAVAILABLE_ANSWER
        if _has_ecoponto_error(response):
            return ECOPONTO_UNAVAILABLE_ANSWER
    return response.answer


def _quote(text: str) -> str:
    lines = text.splitlines() or [""]
    return "\n".join(f"> {line}" if line else ">" for line in lines)


def format_assistant_message(response: AgentResponse) -> str:
    title = status_title(response)
    answer = display_answer(response)
    lines: list[str] = []
    if response.blocked_by_guardrail:
        lines.extend([f"**{title}**", "", _quote(answer)])
    else:
        lines.extend([f"**{title}**", "", answer])

    if response.sources and not response.blocked_by_guardrail:
        lines.extend(["", "**Fontes documentais consultadas:**"])
        lines.extend(
            (
                f"- **[{source.label}]** {source.title} "
                f"(documento: {source.doc_id}; publicado em: "
                f"{source.publication_date}; seção: {source.section})"
            )
            for source in response.sources
        )
    elif _has_document_tool(response) and not response.blocked_by_guardrail:
        lines.extend(
            [
                "",
                "_Nenhuma fonte documental foi recuperada nesta resposta._",
            ]
        )
    return "\n".join(lines)


def format_sources(response: AgentResponse) -> str:
    lines: list[str] = []
    if response.blocked_by_guardrail:
        lines.append(
            "### Fontes documentais\n\n"
            "A resposta foi limitada; nenhuma fonte documental foi "
            "apresentada."
        )
    elif response.sources:
        lines.extend(["### Fontes documentais", ""])
        for source in response.sources:
            lines.extend(
                [
                    f"**[{source.label}] {source.title}**",
                    "",
                    f"- Documento: `{source.doc_id}`",
                    f"- Publicado em: {source.publication_date}",
                    f"- Seção: {source.section}",
                    f"- Arquivo: `{source.source_file}`",
                    "",
                ]
            )
    elif _has_document_tool(response):
        lines.append(
            "### Fontes documentais\n\n"
            "A consulta documental não recuperou fontes para esta resposta."
        )
    else:
        lines.append(
            "### Fontes documentais\n\n"
            "Nenhuma fonte documental foi utilizada nesta resposta."
        )

    if response.tool_calls:
        names: list[str] = []
        for call in response.tool_calls:
            if call.name not in names:
                names.append(call.name)
        lines.extend(
            [
                "### Ferramentas consultadas",
                "",
                ", ".join(f"`{name}`" for name in names),
            ]
        )
    return "\n".join(lines)


def format_status(response: AgentResponse) -> str:
    parts = [f"**Status:** {status_title(response)}."]
    reason = response.stopped_reason

    if reason == "insufficient_context":
        parts.append(
            "A base disponível não trouxe contexto suficiente para uma "
            "resposta segura."
        )
    elif reason == "input_guardrail":
        parts.append(
            "A pergunta foi recusada antes de consultar o modelo ou a base."
        )
    elif reason == "output_guardrail":
        parts.append(
            "A resposta gerada foi bloqueada para evitar conteúdo inseguro."
        )
    elif reason == "tool_call_limit":
        parts.append(
            "O agente atingiu o limite de seis chamadas de ferramentas."
        )
    elif reason == "repeated_tool_call":
        parts.append(
            "O agente detectou uma chamada repetida e interrompeu o fluxo."
        )

    if _is_llm_failure(response):
        parts.append(
            "Verifique a configuração do Ollama local e tente novamente."
        )
    if _is_vector_store_failure(response):
        parts.append(
            "Verifique se a ingestão foi executada e se o banco vetorial "
            "local está acessível."
        )
    if _has_ecoponto_error(response):
        parts.append("Verifique o arquivo data/ecopontos.json.")

    if response.tool_calls:
        names: list[str] = []
        for call in response.tool_calls:
            if call.name not in names:
                names.append(call.name)
        parts.append(
            "Ferramentas consultadas: "
            + ", ".join(f"`{name}`" for name in names)
            + "."
        )
    if response.guardrail_events:
        parts.append(
            "Eventos de guardrail: "
            + ", ".join(f"`{event}`" for event in response.guardrail_events)
            + "."
        )
    return "\n\n".join(parts)


__all__ = [
    "ECOPONTO_UNAVAILABLE_ANSWER",
    "OLLAMA_UNAVAILABLE_ANSWER",
    "VECTOR_STORE_UNAVAILABLE_ANSWER",
    "display_answer",
    "format_assistant_message",
    "format_sources",
    "format_status",
    "status_title",
]
