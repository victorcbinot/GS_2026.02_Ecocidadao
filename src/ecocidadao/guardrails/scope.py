from __future__ import annotations

import re
from dataclasses import dataclass

from .messages import SCOPE_REFUSAL
from .text import contains_term, normalize_text

_DOMAIN_TERMS: dict[str, int] = {
    "ecoponto": 3,
    "ecopontos": 3,
    "descarte": 3,
    "descartar": 3,
    "descarta": 3,
    "descartei": 3,
    "residuo": 3,
    "residuos": 3,
    "reciclagem": 3,
    "reciclar": 3,
    "reciclavel": 3,
    "reciclaveis": 3,
    "coleta seletiva": 3,
    "lixo": 3,
    "lixos": 3,
    "sustentabilidade": 3,
    "sustentavel": 3,
    "meio ambiente": 3,
    "educacao ambiental": 3,
    "compostagem": 3,
    "compostar": 3,
    "logistica reversa": 3,
    "economia circular": 3,
    "parque das acacias": 3,
    "farmacia municipal": 3,
    "economizar agua": 3,
    "economizar energia": 3,
    "consumo consciente": 3,
    "pilha": 2,
    "pilhas": 2,
    "bateria": 2,
    "baterias": 2,
    "eletronico": 2,
    "eletronicos": 2,
    "eletrodomestico": 2,
    "eletrodomesticos": 2,
    "lampada": 2,
    "lampadas": 2,
    "oleo de cozinha": 2,
    "oleo usado": 2,
    "vidro": 2,
    "vidros": 2,
    "papel": 2,
    "papelao": 2,
    "plastico": 2,
    "plasticos": 2,
    "metal": 2,
    "metais": 2,
    "organico": 2,
    "organicos": 2,
    "rejeito": 2,
    "rejeitos": 2,
    "medicamento": 2,
    "medicamentos": 2,
    "remedio": 2,
    "remedios": 2,
    "entulho": 2,
    "entulhos": 2,
    "movel": 2,
    "moveis": 2,
    "pneu": 2,
    "pneus": 2,
    "isopor": 2,
    "esponja": 2,
    "cartucho": 2,
    "toner": 2,
    "tinta": 2,
    "solvente": 2,
    "quimico": 2,
    "quimicos": 2,
    "hospitalar": 2,
    "hospitalares": 2,
    "doacao": 2,
    "doar": 2,
    "reutilizar": 2,
    "reuso": 2,
    "conserto": 2,
    "roupas": 2,
    "calçado": 2,
    "calcados": 2,
    "farmacia": 2,
    "horario": 1,
    "horarios": 1,
    "endereco": 1,
    "enderecos": 1,
    "onde": 1,
    "entregar": 1,
    "entrega": 1,
    "separar": 1,
    "separacao": 1,
    "limite": 1,
    "limites": 1,
    "quantidade": 1,
    "aceita": 1,
    "aceitos": 1,
    "aceitam": 1,
    "proibido": 1,
    "proibidos": 1,
    "interdicao": 1,
    "interditado": 1,
    "reabertura": 1,
    "reabrir": 1,
    "funcionamento": 1,
    "funciona": 1,
    "coleta": 1,
    "prefeitura": 1,
    "secretaria": 1,
    "bairro": 1,
    "domicilio": 1,
    "cidadao": 1,
    "cidade": 1,
    "municipal": 1,
    "agua": 1,
    "energia": 1,
}

_OFF_TOPIC_TERMS: dict[str, int] = {
    "receita": 2,
    "bolo": 3,
    "culinaria": 3,
    "cozinhar": 2,
    "cozinha": 1,
    "futebol": 3,
    "jogo": 2,
    "campeonato": 3,
    "time": 1,
    "jogador": 2,
    "politica": 3,
    "presidente": 3,
    "eleicao": 3,
    "governador": 3,
    "prefeito": 2,
    "programacao": 3,
    "programar": 3,
    "codigo": 2,
    "python": 3,
    "javascript": 3,
    "java": 3,
    "matematica": 3,
    "equacao": 2,
    "filme": 3,
    "serie": 2,
    "musica": 3,
    "novela": 3,
    "ator": 2,
    "viagem": 3,
    "passagem": 2,
    "hotel": 3,
    "voo": 3,
    "investimento": 3,
    "dinheiro": 2,
    "bitcoin": 3,
    "imposto": 3,
    "imposto de renda": 3,
    "receita federal": 3,
    "namoro": 3,
    "relacionamento": 3,
    "amor": 2,
    "doenca": 3,
    "sintoma": 3,
    "diagnostico": 3,
    "tratamento": 3,
    "dor": 2,
    "febre": 3,
    "pressao": 2,
    "emprego": 2,
    "curriculo": 3,
    "salario": 3,
    "vaga": 2,
    "carro": 2,
    "moto": 2,
    "celular": 1,
    "iphone": 3,
    "computador": 1,
    "clima": 2,
    "previsao do tempo": 3,
    "tempo": 1,
    "noticia": 2,
    "historia": 2,
    "geografia": 2,
    "capital": 1,
    "franca": 3,
    "pais": 1,
    "guerra": 3,
    "religiao": 3,
    "piada": 3,
    "conselho": 1,
    "dosagem": 3,
    "receita medica": 3,
}

_OFF_TOPIC_PATTERNS: tuple[tuple[re.Pattern[str], int, str], ...] = (
    (
        re.compile(
            r"\b(comprar|tomar|receitar|indicar|dosagem)\b.{0,40}"
            r"\b(remedio|medicamento)\b"
        ),
        3,
        "uso_medicamento",
    ),
    (
        re.compile(
            r"\b(remedio|medicamento)\b.{0,40}\b(para|de)\b.{0,20}"
            r"\b(dor|doenca|sintoma|febre|pressao)\b"
        ),
        3,
        "indicacao_medicamento",
    ),
    (
        re.compile(r"\b(qual|que)\b.{0,20}\b(remedio|medicamento)\b"),
        2,
        "consulta_medicamento",
    ),
)


@dataclass(frozen=True)
class ScopeAssessment:
    in_scope: bool
    domain_score: int
    off_topic_score: int
    domain_matches: tuple[str, ...]
    off_topic_matches: tuple[str, ...]
    reason: str = ""

    @property
    def safe_response(self) -> str | None:
        return None if self.in_scope else SCOPE_REFUSAL


def _score_terms(
    normalized_text: str,
    terms: dict[str, int],
) -> tuple[int, tuple[str, ...]]:
    score = 0
    matches: list[str] = []
    for term, weight in terms.items():
        if contains_term(normalized_text, term):
            score += weight
            matches.append(term)
    return score, tuple(matches)


def assess_scope(text: str) -> ScopeAssessment:
    normalized = normalize_text(text)
    domain_score, domain_matches = _score_terms(
        normalized,
        _DOMAIN_TERMS,
    )
    off_topic_score, off_topic_matches = _score_terms(
        normalized,
        _OFF_TOPIC_TERMS,
    )

    extra_matches: list[str] = []
    for pattern, weight, label in _OFF_TOPIC_PATTERNS:
        if pattern.search(normalized):
            off_topic_score += weight
            extra_matches.append(label)

    combined_off_topic = off_topic_matches + tuple(extra_matches)
    has_anchor = any(
        _DOMAIN_TERMS[term] >= 2 for term in domain_matches
    )

    if not has_anchor:
        return ScopeAssessment(
            in_scope=False,
            domain_score=domain_score,
            off_topic_score=off_topic_score,
            domain_matches=domain_matches,
            off_topic_matches=combined_off_topic,
            reason="Pergunta sem elementos do domínio de descarte.",
        )

    if off_topic_score >= domain_score and off_topic_score > 0:
        return ScopeAssessment(
            in_scope=False,
            domain_score=domain_score,
            off_topic_score=off_topic_score,
            domain_matches=domain_matches,
            off_topic_matches=combined_off_topic,
            reason="Assunto externo predomina na pergunta.",
        )

    return ScopeAssessment(
        in_scope=True,
        domain_score=domain_score,
        off_topic_score=off_topic_score,
        domain_matches=domain_matches,
        off_topic_matches=combined_off_topic,
    )


__all__ = ["ScopeAssessment", "assess_scope"]
