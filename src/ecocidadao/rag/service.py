from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any, Callable, Protocol

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable

from ..config import Settings, get_settings
from ..guardrails import (
    INSUFFICIENT_CONTEXT_ANSWER,
    GuardrailEngine,
)
from .context import (
    ContextBundle,
    Source,
    build_context,
    extract_date_mentions,
)
from .embeddings import EmbeddingModel
from .llm import create_chat_model
from .prompts import build_prompt
from .vector_store import (
    COLLECTION_NAMES,
    RetrievedChunk,
    load_collection,
)

NO_CONTEXT_ANSWER = INSUFFICIENT_CONTEXT_ANSWER
_CITATION_PATTERN = re.compile(r"\[(F\d+)\]", re.IGNORECASE)
_TEMPORAL_TERMS = (
    "interdi",
    "reabert",
    "vigenc",
    "vigênc",
    "vigen",
    "antes",
    "depois",
    "após",
    "apos",
    "durante",
    "a partir",
    "partir de",
)
TEMPORAL_TOP_K = 10


def is_temporal_question(question: str) -> bool:
    normalized = question.casefold()
    if extract_date_mentions(question):
        return True
    return any(term in normalized for term in _TEMPORAL_TERMS)


class RagServiceError(RuntimeError):
    pass


class VectorStore(Protocol):
    def query(
        self,
        query_text: str,
        top_k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[RetrievedChunk]:
        ...

    def count(self) -> int:
        ...


VectorStoreFactory = Callable[[str], VectorStore]


@dataclass(frozen=True)
class RagResponse:
    question: str
    answer: str
    sources: list[Source]
    cited_sources: list[Source]
    context: str
    temporal_notes: str
    collection_name: str
    as_of: str
    has_sufficient_context: bool
    guardrail_events: tuple[str, ...] = ()
    blocked_by_guardrail: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "answer": self.answer,
            "sources": [source.to_dict() for source in self.sources],
            "cited_sources": [
                source.to_dict() for source in self.cited_sources
            ],
            "collection_name": self.collection_name,
            "as_of": self.as_of,
            "has_sufficient_context": self.has_sufficient_context,
            "temporal_notes": self.temporal_notes,
            "guardrail_events": list(self.guardrail_events),
            "blocked_by_guardrail": self.blocked_by_guardrail,
        }


def resolve_citations(
    answer: str,
    sources: list[Source],
) -> list[Source]:
    by_label = {source.label.upper(): source for source in sources}
    cited: list[Source] = []
    seen: set[str] = set()

    for match in _CITATION_PATTERN.finditer(answer):
        label = match.group(1).upper()
        if label in seen or label not in by_label:
            continue
        seen.add(label)
        cited.append(by_label[label])

    return cited


class RagService:
    def __init__(
        self,
        llm: Runnable | None = None,
        collection_name: str | None = None,
        chroma_dir: Path | str | None = None,
        embedding_model: EmbeddingModel | None = None,
        vector_store_factory: VectorStoreFactory | None = None,
        top_k: int | None = None,
        temporal_top_k: int = TEMPORAL_TOP_K,
        score_threshold: float | None = None,
        max_context_chars: int | None = None,
        now_provider: Callable[[], date] | None = None,
        guardrail_engine: GuardrailEngine | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.default_collection = (
            collection_name or self.settings.collection_name
        )
        self._validate_collection(self.default_collection)
        self.chroma_dir = chroma_dir or self.settings.chroma_dir
        self.embedding_model = embedding_model
        self._vector_store_factory = vector_store_factory
        self._stores: dict[str, VectorStore] = {}
        self.top_k = int(
            self.settings.retrieval_top_k if top_k is None else top_k
        )
        self.temporal_top_k = int(temporal_top_k)
        if self.temporal_top_k < 1:
            raise ValueError("temporal_top_k deve ser maior ou igual a 1.")
        self.score_threshold = (
            float(score_threshold)
            if score_threshold is not None
            else float(self.settings.retrieval_score_threshold)
        )
        self.max_context_chars = int(
            self.settings.max_context_chars
            if max_context_chars is None
            else max_context_chars
        )
        self._now_provider = now_provider or date.today
        self.guardrails = guardrail_engine or GuardrailEngine()
        self._llm = llm
        self._chain: Runnable | None = None

    @property
    def llm(self) -> Runnable:
        if self._llm is None:
            self._llm = create_chat_model(self.settings)
        return self._llm

    @property
    def chain(self) -> Runnable:
        if self._chain is None:
            self._chain = (
                build_prompt()
                | self.llm
                | StrOutputParser()
            )
        return self._chain

    @staticmethod
    def _validate_collection(collection_name: str) -> None:
        if collection_name not in COLLECTION_NAMES:
            allowed = ", ".join(COLLECTION_NAMES)
            raise ValueError(
                f"Colecao invalida: {collection_name!r}. "
                f"Use uma destas: {allowed}."
            )

    def _validate_question(self, question: str) -> str:
        normalized = question.strip()
        if not normalized:
            raise ValueError("A pergunta nao pode ser vazia.")
        if len(normalized) > self.settings.max_input_chars:
            raise ValueError(
                "A pergunta excede o limite de "
                f"{self.settings.max_input_chars} caracteres."
            )
        return normalized

    def _store_for(self, collection_name: str) -> VectorStore:
        if collection_name not in self._stores:
            if self._vector_store_factory is not None:
                self._stores[collection_name] = self._vector_store_factory(
                    collection_name
                )
            else:
                self._stores[collection_name] = load_collection(
                    collection_name=collection_name,
                    chroma_dir=self.chroma_dir,
                    embedding_model=self.embedding_model,
                )
        return self._stores[collection_name]

    def retrieve(
        self,
        question: str,
        collection_name: str | None = None,
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        normalized_question = self._validate_question(question)
        collection = collection_name or self.default_collection
        self._validate_collection(collection)
        requested_top_k = int(self.top_k if top_k is None else top_k)
        if requested_top_k < 1:
            raise ValueError("top_k deve ser maior ou igual a 1.")
        if is_temporal_question(normalized_question):
            requested_top_k = max(requested_top_k, self.temporal_top_k)

        store = self._store_for(collection)
        if store.count() == 0:
            return []

        fetch_k = requested_top_k
        if self.score_threshold > 0.0:
            fetch_k = max(
                requested_top_k,
                int(self.settings.retrieval_fetch_k),
            )

        candidates = store.query(normalized_question, top_k=fetch_k)
        relevant = [
            candidate
            for candidate in candidates
            if candidate.similarity >= self.score_threshold
        ]
        return relevant[:requested_top_k]

    def _resolve_as_of(self, as_of: date | str | None) -> str:
        if as_of is None:
            return self._now_provider().isoformat()
        if isinstance(as_of, date):
            return as_of.isoformat()
        try:
            return date.fromisoformat(as_of).isoformat()
        except ValueError as error:
            raise ValueError(
                "as_of deve estar no formato ISO AAAA-MM-DD."
            ) from error

    @staticmethod
    def _merge_events(*groups: tuple[str, ...]) -> tuple[str, ...]:
        merged: list[str] = []
        for group in groups:
            for event in group:
                if event not in merged:
                    merged.append(event)
        return tuple(merged)

    def _guardrail_response(
        self,
        question: str,
        answer: str,
        collection: str,
        as_of: str,
        events: tuple[str, ...],
        temporal_notes: str = "",
        context: str = "",
        blocked: bool = True,
    ) -> RagResponse:
        return RagResponse(
            question=question,
            answer=answer,
            sources=[],
            cited_sources=[],
            context=context,
            temporal_notes=temporal_notes,
            collection_name=collection,
            as_of=as_of,
            has_sufficient_context=False,
            guardrail_events=self._merge_events(events),
            blocked_by_guardrail=blocked,
        )

    def ask(
        self,
        question: str,
        collection_name: str | None = None,
        top_k: int | None = None,
        as_of: date | str | None = None,
    ) -> RagResponse:
        normalized_question = self._validate_question(question)
        collection = collection_name or self.default_collection
        self._validate_collection(collection)
        as_of_iso = self._resolve_as_of(as_of)

        input_result = self.guardrails.check_input(normalized_question)
        if input_result.blocked:
            return self._guardrail_response(
                question=input_result.question,
                answer=input_result.safe_response or NO_CONTEXT_ANSWER,
                collection=collection,
                as_of=as_of_iso,
                events=input_result.events,
                blocked=True,
            )

        effective_question = input_result.question
        retrieved = self.retrieve(
            effective_question,
            collection_name=collection,
            top_k=top_k,
        )
        context_scan = self.guardrails.sanitize_context(
            [chunk.text for chunk in retrieved]
        )
        sanitized_retrieved = [
            replace(chunk, text=text)
            for chunk, text in zip(retrieved, context_scan.texts)
            if text.strip()
        ]
        bundle = build_context(
            question=effective_question,
            retrieved=sanitized_retrieved,
            as_of=as_of_iso,
            max_chars=self.max_context_chars,
        )
        base_events = self._merge_events(
            input_result.events,
            context_scan.events,
        )

        if not bundle.sources:
            return self._guardrail_response(
                question=effective_question,
                answer=NO_CONTEXT_ANSWER,
                collection=collection,
                as_of=as_of_iso,
                events=self._merge_events(
                    base_events,
                    ("insufficient_context",),
                ),
                temporal_notes=bundle.temporal_notes,
                blocked=True,
            )

        chain = self.chain
        try:
            answer = chain.invoke(
                {
                    "question": effective_question,
                    "as_of": bundle.as_of,
                    "question_dates": (
                        ", ".join(bundle.question_dates)
                        if bundle.question_dates
                        else "nenhuma"
                    ),
                    "temporal_notes": bundle.temporal_notes,
                    "context": bundle.text,
                }
            )
        except Exception as error:
            raise RagServiceError(
                f"Falha ao consultar o modelo de linguagem: {error}"
            ) from error

        answer_text = str(answer).strip()
        output_result = self.guardrails.validate_output(
            question=effective_question,
            answer=answer_text,
            valid_labels=[source.label for source in bundle.sources],
        )
        events = self._merge_events(base_events, output_result.events)

        if output_result.used_fallback or not output_result.allowed:
            return self._guardrail_response(
                question=effective_question,
                answer=output_result.answer,
                collection=collection,
                as_of=as_of_iso,
                events=events,
                temporal_notes=bundle.temporal_notes,
                blocked=True,
            )

        if output_result.is_limitation:
            return self._guardrail_response(
                question=effective_question,
                answer=output_result.answer,
                collection=collection,
                as_of=as_of_iso,
                events=self._merge_events(
                    events,
                    ("insufficient_context",),
                ),
                temporal_notes=bundle.temporal_notes,
                blocked=True,
            )

        cited_sources = resolve_citations(
            output_result.answer,
            bundle.sources,
        )

        return RagResponse(
            question=effective_question,
            answer=output_result.answer,
            sources=bundle.sources,
            cited_sources=cited_sources,
            context=bundle.text,
            temporal_notes=bundle.temporal_notes,
            collection_name=collection,
            as_of=as_of_iso,
            has_sufficient_context=bool(cited_sources),
            guardrail_events=events,
            blocked_by_guardrail=False,
        )

    def build_context(
        self,
        question: str,
        retrieved: list[RetrievedChunk],
        as_of: date | str | None = None,
    ) -> ContextBundle:
        return build_context(
            question=self._validate_question(question),
            retrieved=retrieved,
            as_of=self._resolve_as_of(as_of),
            max_chars=self.max_context_chars,
        )


__all__ = [
    "NO_CONTEXT_ANSWER",
    "TEMPORAL_TOP_K",
    "RagResponse",
    "RagService",
    "RagServiceError",
    "VectorStore",
    "VectorStoreFactory",
    "is_temporal_question",
    "resolve_citations",
]
