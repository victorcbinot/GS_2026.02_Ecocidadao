from __future__ import annotations

import re
from dataclasses import dataclass

from .messages import PROMPT_INJECTION_REFUSAL, REMOVED_INSTRUCTION
from .text import normalize_text

_INJECTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "override_instructions",
        re.compile(
            r"\b(ignore|ignorar|desconsidere|desconsiderar|esqueca|"
            r"esquecer|sobrescreva|abandone|descarte)\b.{0,80}"
            r"\b(instrucoes|prompt|comandos|regras de sistema|"
            r"regras anteriores|regras acima|mensagem de sistema)\b"
        ),
    ),
    (
        "ignore_context",
        re.compile(
            r"\b(ignore|ignorar|desconsidere|desconsiderar|abandone)\b"
            r".{0,60}\b(contexto|documentos|fontes|trechos)\b"
        ),
    ),
    (
        "reveal_prompt",
        re.compile(
            r"\b(revele|revelar|mostre|mostrar|exiba|exibir|imprima|"
            r"imprimir|repita|repetir|qual e|qual o)\b.{0,60}"
            r"\b(prompt|instrucoes do sistema|mensagem de sistema|"
            r"regras de sistema|configuracoes internas)\b"
        ),
    ),
    (
        "role_change",
        re.compile(
            r"\b(aja como|atue como|finja que|faca de conta que|"
            r"voce agora e|a partir de agora voce|assuma o papel|"
            r"sua nova tarefa|novo papel)\b"
        ),
    ),
    (
        "developer_mode",
        re.compile(
            r"\b(modo desenvolvedor|developer mode|jailbreak|"
            r"modo sem restricoes|sem filtros|sem guardrails)\b"
        ),
    ),
    (
        "bypass_security",
        re.compile(
            r"\b(bypass|contorne|contornar|desative|desativar|"
            r"desabilite|desabilitar)\b.{0,40}"
            r"\b(guardrail|guardrails|filtro|filtros|seguranca|"
            r"regras|restricoes)\b"
        ),
    ),
    (
        "fake_evidence",
        re.compile(
            r"\b(responda sem citar|nao cite|nao use o contexto|"
            r"nao use as fontes|invente|inventar|crie)\b.{0,50}"
            r"\b(fonte|fontes|citacao|citas|citatura|documento|"
            r"documentos|evidencia)\b"
        ),
    ),
    (
        "secret_exfiltration",
        re.compile(
            r"\b(chave da api|api key|token de acesso|access token|"
            r"senha do sistema|credenciais|segredo interno)\b"
        ),
    ),
    (
        "system_override",
        re.compile(
            r"\b(nao siga|nao obedeca|sobrescreva|substitua)\b.{0,50}"
            r"\b(regras|instrucoes|orientacoes|politicas)\b"
        ),
    ),
)

_ASSISTANT_CONTEXT = re.compile(
    r"\b(assistente|modelo|ia|chatgpt|llm|sistema|prompt)\b"
)


@dataclass(frozen=True)
class InjectionFinding:
    category: str
    matched_text: str


@dataclass(frozen=True)
class DocumentScanResult:
    text: str
    findings: tuple[InjectionFinding, ...]
    removed_lines: int
    dropped: bool

    @property
    def sanitized(self) -> bool:
        return bool(self.findings)

    @property
    def safe_response(self) -> str | None:
        return PROMPT_INJECTION_REFUSAL if self.findings else None


@dataclass(frozen=True)
class ContextScanResult:
    texts: tuple[str, ...]
    findings: tuple[InjectionFinding, ...]
    sanitized_chunks: int
    dropped_chunks: int
    redacted_chunks: int = 0

    @property
    def sanitized(self) -> bool:
        return bool(self.findings)

    @property
    def events(self) -> tuple[str, ...]:
        events: list[str] = []
        if self.findings:
            events.append("document_injection_sanitized")
        if self.redacted_chunks:
            events.append("context_personal_data_redacted")
        return tuple(events)


def detect_prompt_injection(text: str) -> tuple[InjectionFinding, ...]:
    normalized = normalize_text(text)
    findings: list[InjectionFinding] = []
    for category, pattern in _INJECTION_PATTERNS:
        match = pattern.search(normalized)
        if match:
            findings.append(
                InjectionFinding(
                    category=category,
                    matched_text=match.group(0),
                )
            )

    if (
        _ASSISTANT_CONTEXT.search(normalized)
        and re.search(
            r"\b(ignore|desconsidere|sobrescreva|revele)\b",
            normalized,
        )
    ):
        if not any(
            finding.category == "override_instructions"
            for finding in findings
        ):
            findings.append(
                InjectionFinding(
                    category="assistant_override",
                    matched_text="instrução dirigida ao assistente",
                )
            )

    return tuple(findings)


def sanitize_document_text(text: str) -> DocumentScanResult:
    findings: list[InjectionFinding] = []
    sanitized_lines: list[str] = []
    original_lines = [line for line in text.splitlines() if line.strip()]
    removed_lines = 0

    for line in text.splitlines():
        line_findings = detect_prompt_injection(line)
        if line_findings:
            findings.extend(line_findings)
            sanitized_lines.append(REMOVED_INSTRUCTION)
            removed_lines += 1
        else:
            sanitized_lines.append(line)

    sanitized_text = "\n".join(sanitized_lines).strip()
    dropped = False
    if findings and (
        len(sanitized_text) < 40
        or (
            original_lines
            and removed_lines >= len(original_lines)
        )
    ):
        sanitized_text = ""
        dropped = True

    return DocumentScanResult(
        text=sanitized_text,
        findings=tuple(findings),
        removed_lines=removed_lines,
        dropped=dropped,
    )


def sanitize_context_texts(texts: list[str] | tuple[str, ...]) -> ContextScanResult:
    sanitized_texts: list[str] = []
    findings: list[InjectionFinding] = []
    sanitized_chunks = 0
    dropped_chunks = 0

    for text in texts:
        result = sanitize_document_text(text)
        if result.findings:
            sanitized_chunks += 1
            findings.extend(result.findings)
        if result.dropped:
            dropped_chunks += 1
        sanitized_texts.append(result.text)

    return ContextScanResult(
        texts=tuple(sanitized_texts),
        findings=tuple(findings),
        sanitized_chunks=sanitized_chunks,
        dropped_chunks=dropped_chunks,
    )


__all__ = [
    "ContextScanResult",
    "DocumentScanResult",
    "InjectionFinding",
    "detect_prompt_injection",
    "sanitize_context_texts",
    "sanitize_document_text",
]
