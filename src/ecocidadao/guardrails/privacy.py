from __future__ import annotations

import re
from dataclasses import dataclass

from .messages import LGPD_REFUSAL, PERSONAL_DATA_REDACTION
from .text import contains_term, normalize_text

_SENSITIVE_TERMS: dict[str, int] = {
    "cpf": 3,
    "rg": 3,
    "cnh": 3,
    "passaporte": 3,
    "titulo de eleitor": 3,
    "telefone": 2,
    "telefone residencial": 3,
    "celular": 2,
    "whatsapp": 3,
    "email": 2,
    "e-mail": 2,
    "endereco residencial": 3,
    "data de nascimento": 3,
    "dados bancarios": 3,
    "cartao de credito": 3,
    "senha": 3,
    "prontuario": 3,
    "ficha medica": 3,
    "biometria": 3,
    "foto": 2,
    "geolocalizacao": 3,
    "matricula": 2,
    "salario": 3,
    "nome completo": 2,
    "dados pessoais": 3,
    "informacoes pessoais": 3,
}

_THIRD_PARTY_PATTERN = re.compile(
    r"\b(?:do|da|dos|das|de|de um|de uma)\s+"
    r"(?:cidadao|cidada|cidadaos|cidadas|morador|moradora|"
    r"moradores|moradoras|vizinho|vizinha|vizinhos|vizinhas|"
    r"proprietario|proprietaria|proprietarios|proprietarias|"
    r"funcionario|funcionaria|funcionarios|funcionarias|"
    r"servidor|servidora|servidores|servidoras|cliente|clientes|"
    r"usuario|usuarios|pessoa|pessoas|alguem|terceiro|terceira|"
    r"terceiros|terceiras|prefeito|prefeita|secretario|"
    r"responsavel|responsaveis|joao|maria|jose|ana|"
    r"carlos|paulo|fernanda|lucas|julia)\b"
)

_IDENTIFICATION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\bquem (mora|reside|trabalha|e o dono|e a dona|"
        r"e o responsavel)\b"
    ),
    re.compile(
        r"\b(onde|em que endereco)\b.{0,30}\b(mora|reside)\b"
    ),
    re.compile(
        r"\b(endereco|telefone|celular|email|cpf|rg)\b.{0,40}"
        r"\b(de|do|da|dos|das)\b.{0,30}"
        r"\b(cidadao|morador|vizinho|pessoa|alguem|joao|maria|"
        r"jose|ana|carlos|paulo|fernanda|lucas|julia)\b"
    ),
    re.compile(
        r"\b(lista|relacao|base|banco)\b.{0,30}"
        r"\b(cidadaos|moradores|usuarios|clientes|pessoas)\b"
    ),
)

_REQUEST_PATTERN = re.compile(
    r"\b(me de|me passe|me informe|me envie|me mostre|me diga|"
    r"informe|revele|liste|quais|qual|preciso|quero|obter|"
    r"consultar|compartilhe|descubra|procure|localize)\b"
)

_CPF_PATTERN = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
_CNPJ_PATTERN = re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b")
_RG_PATTERN = re.compile(r"\b\d{1,2}\.?\d{3}\.?\d{3}-?[\dXx]\b")
_PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+?55\s*)?(?:\(?\d{2}\)?\s*)?"
    r"(?:9?\d{4})[-\s]?(?:\d{4})(?!\d)"
)
_EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)


@dataclass(frozen=True)
class PrivacyAssessment:
    blocked: bool
    reason: str = ""
    matches: tuple[str, ...] = ()

    @property
    def safe_response(self) -> str | None:
        return LGPD_REFUSAL if self.blocked else None


def _sensitive_terms(normalized_text: str) -> tuple[str, ...]:
    return tuple(
        term
        for term in _SENSITIVE_TERMS
        if contains_term(normalized_text, term)
    )


def assess_privacy(question: str) -> PrivacyAssessment:
    normalized = normalize_text(question)
    sensitive = _sensitive_terms(normalized)
    third_party = bool(_THIRD_PARTY_PATTERN.search(normalized))
    identification = any(
        pattern.search(normalized) for pattern in _IDENTIFICATION_PATTERNS
    )
    if identification:
        return PrivacyAssessment(
            blocked=True,
            reason="Tentativa de identificar ou localizar pessoa.",
            matches=("identificacao_de_pessoa",),
        )

    if third_party and sensitive:
        return PrivacyAssessment(
            blocked=True,
            reason="Solicitação de dado pessoal de terceiro.",
            matches=tuple(sensitive) + ("terceiro",),
        )

    if third_party and _REQUEST_PATTERN.search(normalized):
        return PrivacyAssessment(
            blocked=True,
            reason="Solicitação de informação sobre pessoa identificada.",
            matches=("terceiro",),
        )

    if "dados pessoais" in sensitive and third_party:
        return PrivacyAssessment(
            blocked=True,
            reason="Solicitação de dados pessoais de terceiros.",
            matches=tuple(sensitive),
        )

    return PrivacyAssessment(blocked=False)


def redact_sensitive_data(text: str) -> tuple[str, bool]:
    redacted = text
    for pattern in (
        _CPF_PATTERN,
        _CNPJ_PATTERN,
        _RG_PATTERN,
        _PHONE_PATTERN,
        _EMAIL_PATTERN,
    ):
        redacted = pattern.sub(PERSONAL_DATA_REDACTION, redacted)
    return redacted, redacted != text


def contains_sensitive_data(text: str) -> bool:
    return any(
        pattern.search(text)
        for pattern in (
            _CPF_PATTERN,
            _CNPJ_PATTERN,
            _RG_PATTERN,
            _PHONE_PATTERN,
            _EMAIL_PATTERN,
        )
    )


__all__ = [
    "PrivacyAssessment",
    "assess_privacy",
    "contains_sensitive_data",
    "redact_sensitive_data",
]
