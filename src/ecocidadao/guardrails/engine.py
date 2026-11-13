from __future__ import annotations

from dataclasses import dataclass, replace

from .injection import (
    ContextScanResult,
    detect_prompt_injection,
    sanitize_context_texts,
)
from .messages import (
    LGPD_REFUSAL,
    PROMPT_INJECTION_REFUSAL,
    SCOPE_REFUSAL,
)
from .output import OutputAssessment, validate_output
from .privacy import assess_privacy, redact_sensitive_data
from .scope import ScopeAssessment, assess_scope


@dataclass(frozen=True)
class InputGuardrailResult:
    question: str
    allowed: bool
    safe_response: str | None
    events: tuple[str, ...]
    findings: tuple[str, ...] = ()

    @property
    def blocked(self) -> bool:
        return not self.allowed


class GuardrailEngine:
    def check_input(self, question: str) -> InputGuardrailResult:
        events: list[str] = []
        findings: list[str] = []

        sanitized_question, redacted = redact_sensitive_data(question)
        if redacted:
            events.append("input_personal_data_redacted")

        injection = detect_prompt_injection(sanitized_question)
        if injection:
            findings.extend(
                finding.category for finding in injection
            )
            return InputGuardrailResult(
                question=sanitized_question,
                allowed=False,
                safe_response=PROMPT_INJECTION_REFUSAL,
                events=tuple(
                    dict.fromkeys(
                        events + ["input_injection_blocked"]
                    )
                ),
                findings=tuple(findings),
            )

        privacy = assess_privacy(sanitized_question)
        if privacy.blocked:
            findings.extend(privacy.matches)
            return InputGuardrailResult(
                question=sanitized_question,
                allowed=False,
                safe_response=LGPD_REFUSAL,
                events=tuple(
                    dict.fromkeys(events + ["input_lgpd_blocked"])
                ),
                findings=tuple(findings),
            )

        scope = assess_scope(sanitized_question)
        if not scope.in_scope:
            findings.extend(scope.domain_matches)
            return InputGuardrailResult(
                question=sanitized_question,
                allowed=False,
                safe_response=SCOPE_REFUSAL,
                events=tuple(
                    dict.fromkeys(events + ["input_scope_blocked"])
                ),
                findings=tuple(findings),
            )

        return InputGuardrailResult(
            question=sanitized_question,
            allowed=True,
            safe_response=None,
            events=tuple(dict.fromkeys(events)),
            findings=tuple(findings),
        )

    def sanitize_context(
        self,
        texts: list[str] | tuple[str, ...],
    ) -> ContextScanResult:
        scan = sanitize_context_texts(texts)
        redacted_texts: list[str] = []
        redacted_chunks = 0
        for text in scan.texts:
            redacted_text, changed = redact_sensitive_data(text)
            if changed:
                redacted_chunks += 1
            redacted_texts.append(redacted_text)
        return replace(
            scan,
            texts=tuple(redacted_texts),
            redacted_chunks=redacted_chunks,
        )

    def validate_output(
        self,
        question: str,
        answer: str,
        valid_labels: list[str] | tuple[str, ...],
        require_citation: bool = True,
    ) -> OutputAssessment:
        return validate_output(
            question,
            answer,
            valid_labels,
            require_citation=require_citation,
        )

    def assess_scope(self, text: str) -> ScopeAssessment:
        return assess_scope(text)


__all__ = [
    "GuardrailEngine",
    "InputGuardrailResult",
]
