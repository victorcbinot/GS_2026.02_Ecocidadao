from __future__ import annotations

import inspect
from typing import Any

import gradio as gr

from ..agent import ChatSession, EcoCidadaoAgent
from ..config import Settings, get_settings
from .presentation import (
    format_assistant_message,
    format_sources,
    format_status,
)

STARTUP_ERROR_MESSAGE = (
    "Não foi possível inicializar os serviços do EcoCidadão. "
    "Verifique o arquivo data/ecopontos.json, as variáveis de ambiente e "
    "a instalação das dependências."
)

PROCESSING_ERROR_MESSAGE = (
    "Não foi possível concluir a solicitação neste momento. "
    "Tente novamente. Se o problema continuar, verifique a conexão com o "
    "Ollama local e a disponibilidade do banco vetorial."
)

INITIAL_STATUS = "**Status:** pronto para receber uma pergunta."
INITIAL_SOURCES = (
    "### Fontes documentais\n\n"
    "As fontes aparecerão aqui após a primeira consulta."
)


def _chatbot() -> gr.Chatbot:
    parameters = inspect.signature(gr.Chatbot).parameters
    kwargs: dict[str, Any] = {
        "label": "Conversa",
        "height": 430,
        "show_label": True,
    }
    if "type" in parameters:
        kwargs["type"] = "messages"
    return gr.Chatbot(**kwargs)


def _message_content(message: Any) -> str:
    if isinstance(message, dict):
        return str(message.get("content") or "")
    return str(getattr(message, "content", "") or "")


def _message_role(message: Any) -> str:
    if isinstance(message, dict):
        return str(message.get("role") or "assistant")
    return str(getattr(message, "role", "assistant") or "assistant")


def _normalize_history(history: Any) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for message in history or []:
        normalized.append(
            {
                "role": _message_role(message),
                "content": _message_content(message),
            }
        )
    return normalized


def _append_exchange(
    history: Any,
    question: str,
    answer: str,
) -> list[dict[str, str]]:
    messages = _normalize_history(history)
    messages.append({"role": "user", "content": question})
    messages.append({"role": "assistant", "content": answer})
    return messages


def _display_error(message: str) -> str:
    return f"**Serviço indisponível**\n\n> {message}"


def _respond(
    question: str,
    history: Any,
    session: ChatSession | None,
    *,
    agent: EcoCidadaoAgent | None,
    startup_error: str | None,
) -> tuple[
    str,
    list[dict[str, str]],
    ChatSession | None,
    str,
    str,
]:
    normalized = (question or "").strip()
    messages = _normalize_history(history)
    if not normalized:
        return (
            "",
            messages,
            session,
            INITIAL_SOURCES,
            "**Status:** digite uma pergunta para começar.",
        )

    if agent is None or (session is None and startup_error):
        answer = startup_error or STARTUP_ERROR_MESSAGE
        return (
            "",
            _append_exchange(messages, normalized, _display_error(answer)),
            session,
            "### Fontes documentais\n\nNenhuma consulta realizada.",
            f"**Status:** serviço indisponível.\n\n{answer}",
        )

    if session is None:
        session = ChatSession(agent=agent)

    try:
        response = session.ask(normalized)
    except ValueError as error:
        answer = (
            "**Não foi possível processar a pergunta**\n\n"
            f"> {error}"
        )
        return (
            "",
            _append_exchange(messages, normalized, answer),
            session,
            "### Fontes documentais\n\nNenhuma consulta realizada.",
            "**Status:** pergunta inválida.",
        )
    except Exception:
        answer = _display_error(PROCESSING_ERROR_MESSAGE)
        return (
            "",
            _append_exchange(messages, normalized, answer),
            session,
            "### Fontes documentais\n\nNenhuma consulta realizada.",
            "**Status:** falha interna ao processar a solicitação.",
        )

    return (
        "",
        _append_exchange(
            messages,
            normalized,
            format_assistant_message(response),
        ),
        session,
        format_sources(response),
        format_status(response),
    )


def _clear(
    session: ChatSession | None,
) -> tuple[list[dict[str, str]], str, str, None]:
    if session is not None:
        session.clear()
    return [], INITIAL_SOURCES, "**Status:** conversa limpa.", None


def build_demo(
    agent: EcoCidadaoAgent | None = None,
    settings: Settings | None = None,
    startup_error: str | None = None,
) -> gr.Blocks:
    settings = settings or get_settings()
    if agent is None and startup_error is None:
        try:
            agent = EcoCidadaoAgent(settings=settings)
        except Exception:
            startup_error = STARTUP_ERROR_MESSAGE

    def handle_submit(
        question: str,
        history: Any,
        session: ChatSession | None,
    ) -> tuple[
        str,
        list[dict[str, str]],
        ChatSession | None,
        str,
        str,
    ]:
        return _respond(
            question,
            history,
            session,
            agent=agent,
            startup_error=startup_error,
        )

    with gr.Blocks(title="EcoCidadão") as demo:
        gr.Markdown(
            "# EcoCidadão\n"
            "Assistente virtual para descarte de resíduos, reciclagem, "
            "sustentabilidade municipal e Ecopontos de EcoCidade."
        )
        if startup_error:
            gr.Markdown(
                "> **Serviço indisponível**\n>\n"
                f"> {startup_error}"
            )

        with gr.Row():
            with gr.Column(scale=3):
                chatbot = _chatbot()
                question = gr.Textbox(
                    label="Sua pergunta",
                    placeholder=(
                        "Ex.: Onde posso descartar pilhas e baterias?"
                    ),
                    lines=2,
                    max_lines=5,
                    interactive=agent is not None,
                )
                with gr.Row():
                    submit = gr.Button(
                        "Enviar",
                        variant="primary",
                        interactive=agent is not None,
                    )
                    clear = gr.Button("Limpar conversa")
                gr.Markdown(
                    "As respostas podem usar documentos oficiais, dados "
                    "estruturados dos Ecopontos e cálculos estimados. "
                    "Os guardrails podem recusar solicitações fora do escopo "
                    "ou sem contexto suficiente."
                )
            with gr.Column(scale=2):
                status = gr.Markdown(INITIAL_STATUS)
                sources = gr.Markdown(INITIAL_SOURCES)
                with gr.Accordion("Sobre o EcoCidadão", open=False):
                    gr.Markdown(
                        "O histórico da conversa é mantido apenas nesta "
                        "sessão do navegador. Perguntas anteriores são usadas "
                        "como contexto, mas não podem alterar as regras de "
                        "segurança. Nenhuma chave de API é exibida."
                    )

        if agent is not None:
            gr.Examples(
                examples=[
                    "Onde posso descartar pilhas e baterias?",
                    "O Parque das Acácias está aberto atualmente?",
                    "Quais materiais o Ecoponto Centro aceita?",
                    "Se eu tiver 3 caixas de 12 kg, qual é o peso total?",
                ],
                inputs=question,
                label="Exemplos de perguntas",
            )

        session_state = gr.State(None)
        submit.click(
            handle_submit,
            inputs=[question, chatbot, session_state],
            outputs=[question, chatbot, session_state, sources, status],
        )
        question.submit(
            handle_submit,
            inputs=[question, chatbot, session_state],
            outputs=[question, chatbot, session_state, sources, status],
        )
        clear.click(
            _clear,
            inputs=[session_state],
            outputs=[chatbot, sources, status, session_state],
        )
    return demo


__all__ = [
    "INITIAL_SOURCES",
    "INITIAL_STATUS",
    "PROCESSING_ERROR_MESSAGE",
    "STARTUP_ERROR_MESSAGE",
    "build_demo",
]
