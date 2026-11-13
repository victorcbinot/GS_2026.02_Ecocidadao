from __future__ import annotations

from datetime import date

from .agent import AgentResponse, ConversationTurn, EcoCidadaoAgent


class ChatSession:
    def __init__(
        self,
        agent: EcoCidadaoAgent,
        max_history_turns: int = 4,
    ) -> None:
        if max_history_turns < 0:
            raise ValueError("max_history_turns não pode ser negativo.")
        self.agent = agent
        self.max_history_turns = int(max_history_turns)
        self._turns: list[ConversationTurn] = []

    @property
    def turns(self) -> tuple[ConversationTurn, ...]:
        return tuple(self._turns)

    def ask(
        self,
        question: str,
        as_of: date | str | None = None,
    ) -> AgentResponse:
        history = (
            tuple(self._turns[-self.max_history_turns :])
            if self.max_history_turns
            else ()
        )
        response = self.agent.ask(
            question,
            as_of=as_of,
            history=history,
        )
        self._turns.append(
            ConversationTurn(
                question=response.question,
                answer=response.answer,
                blocked_by_guardrail=response.blocked_by_guardrail,
                stopped_reason=response.stopped_reason,
            )
        )
        return response

    def clear(self) -> None:
        self._turns.clear()


__all__ = ["ChatSession"]
