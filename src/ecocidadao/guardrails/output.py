from __future__ import annotations

import re
from dataclasses import dataclass

from .injection import detect_prompt_injection
from .messages import (
    INSUFFICIENT_CONTEXT_ANSWER,
    OUTPUT_FALLBACK_ANSWER,
    PROMPT_INJECTION_REFUSAL,
    SCOPE_REFUSAL,
)
from .privacy import redact_sensitive_data
from .scope import assess_scope
from .text import normalize_text

_CITATION_PATTERN = re.compile(r"\[(F\d+)\]", re.IGNORECASE)
_LIMITATION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bnao encontrei informacoes suficientes\b"),
    re.compile(r"\bnao ha informacao suficiente\b"),
    re.compile(r"\bnao ha informacoes suficientes\b"),
    re.compile(r"\bnao consta\b"),
    re.compile(r"\bnao tenho informacao\b"),
    re.compile(r"\bnao tenho informacoes\b"),
    re.compile(r"\bbase documental nao\b"),
    re.compile(r"\bsem informacao suficiente\b"),
    re.compile(r"\bnao posso responder com seguranca\b"),
    re.compile(r"\bnao foi possivel encontrar\b"),
)
_OUTPUT_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(meu|o|este)\s+prompt\s+(do sistema\s+)?"
        r"(e|foi|diz|contem|inclui)\b"
    ),
    re.compile(
        r"\b(minhas|as)\s+instrucoes\s+(do sistema\s+)?"
        r"(sao|foram|dizem|incluem)\b"
    ),
    re.compile(
        r"\b(ignore|desconsidere)\s+(as\s+)?instrucoes\s+"
        r"(anteriores|do sistema)\b"
    ),
    re.compile(r"\b(modo desenvolvedor|developer mode|jailbreak)\b"),
    re.compile(r"\bvoce agora e\b"),
)


@dataclass(frozen=True)
class OutputAssessment:
    answer: str
    allowed: bool
    events: tuple[str, ...]
    invalid_citations: tuple[str, ...] = ()
    is_limitation: bool = False
    used_fallback: bool = False
    blocked: bool = False

    @property
    def safe_response(self) -> str | None:
        return self.answer if self.blocked else None


def extract_citations(answer: str) -> tuple[str, ...]:
    labels: list[str] = []
    seen: set[str] = set()
    for match in _CITATION_PATTERN.finditer(answer):
        label = match.group(1).upper()
        if label not in seen:
            seen.add(label)
            labels.append(label)
    return tuple(labels)


def remove_invalid_citations(
    answer: str,
    valid_labels: set[str],
) -> tuple[str, tuple[str, ...]]:
    invalid: list[str] = []

    def replace(match: re.Match[str]) -> str:
        label = match.group(1).upper()
        if label in valid_labels:
            return match.group(0)
        if label not in invalid:
            invalid.append(label)
        return ""

    cleaned = _CITATION_PATTERN.sub(replace, answer)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([.,;:!?])", r"\1", cleaned)
    return cleaned.strip(), tuple(invalid)


def is_limitation_answer(answer: str) -> bool:
    normalized = normalize_text(answer)
    return any(
        pattern.search(normalized) for pattern in _LIMITATION_PATTERNS
    )


def _contains_output_injection(answer: str) -> bool:
    normalized = normalize_text(answer)
    return any(
        pattern.search(normalized)
        for pattern in _OUTPUT_INJECTION_PATTERNS
    )


def _fallback(
    events: list[str],
    *,
    invalid_citations: tuple[str, ...] = (),
    blocked: bool = True,
    answer: str = OUTPUT_FALLBACK_ANSWER,
) -> OutputAssessment:
    return OutputAssessment(
        answer=answer,
        allowed=False,
        events=tuple(dict.fromkeys(events)),
        invalid_citations=invalid_citations,
        used_fallback=True,
        blocked=blocked,
    )


def validate_output(
    question: str,
    answer: str,
    valid_labels: list[str] | tuple[str, ...],
    require_citation: bool = True,
) -> OutputAssessment:
    events: list[str] = []
    cleaned = answer.strip()
    if not cleaned:
        return _fallback(["output_empty"], blocked=True)

    cleaned, redacted = redact_sensitive_data(cleaned)
    if redacted:
        events.append("personal_data_redacted")

    valid_set = {label.upper() for label in valid_labels}
    cleaned, invalid_citations = remove_invalid_citations(
        cleaned,
        valid_set,
    )
    if invalid_citations:
        events.append("invalid_citations_removed")

    if _contains_output_injection(cleaned):
        return _fallback(
            events + ["output_injection_blocked"],
            blocked=True,
            answer=PROMPT_INJECTION_REFUSAL,
        )

    limitation = is_limitation_answer(cleaned)
    if limitation:
        return OutputAssessment(
            answer=INSUFFICIENT_CONTEXT_ANSWER,
            allowed=True,
            events=tuple(
                dict.fromkeys(events + ["insufficient_context"])
            ),
            invalid_citations=invalid_citations,
            is_limitation=True,
            used_fallback=False,
            blocked=False,
        )

    scope = assess_scope(cleaned)
    if (
        scope.off_topic_score > 0
        and scope.off_topic_score >= scope.domain_score
    ):
        return _fallback(
            events + ["output_scope_blocked"],
            invalid_citations=invalid_citations,
            blocked=True,
            answer=SCOPE_REFUSAL,
        )

    if require_citation and not extract_citations(cleaned):
        return _fallback(
            events + ["output_without_evidence"],
            invalid_citations=invalid_citations,
            blocked=True,
        )

    return OutputAssessment(
        answer=cleaned,
        allowed=True,
        events=tuple(dict.fromkeys(events)),
        invalid_citations=invalid_citations,
        is_limitation=False,
        used_fallback=False,
        blocked=False,
    )


__all__ = [
    "OutputAssessment",
    "extract_citations",
    "is_limitation_answer",
    "remove_invalid_citations",
    "validate_output",
]
