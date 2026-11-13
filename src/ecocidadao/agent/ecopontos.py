from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any

from ..guardrails.text import normalize_text


class EcopontoDataError(ValueError):
    pass


@dataclass(frozen=True)
class Ecoponto:
    id: str
    nome: str
    endereco: str
    horario: str
    materiais_aceitos: tuple[str, ...]
    materiais_nao_aceitos: tuple[str, ...]
    situacao: str


@dataclass(frozen=True)
class Comunicado:
    id: str
    ecoponto_id: str
    publicado_em: date
    interdicao_inicio: date
    interdicao_fim: date
    reabertura_em: date
    horario_apos_reabertura: str
    materiais_aceitos_apos_reabertura: tuple[str, ...]
    materiais_removidos_apos_reabertura: tuple[str, ...]
    alternativas_durante_interdicao: tuple[str, ...]
    observacao: str


@dataclass(frozen=True)
class EcopontoStatus:
    ecoponto: Ecoponto
    as_of: date
    situacao: str
    horario: str
    materiais_aceitos: tuple[str, ...]
    materiais_nao_aceitos: tuple[str, ...]
    material_consultado: str = ""
    aceita_material: bool | None = None
    aviso: str = ""
    alternativas: tuple[str, ...] = ()


@dataclass(frozen=True)
class EcopontoCatalog:
    municipio: str
    fonte: dict[str, Any]
    observacoes: tuple[str, ...]
    ecopontos: tuple[Ecoponto, ...]
    comunicados: tuple[Comunicado, ...]

    @classmethod
    def load(cls, path: Path | str) -> EcopontoCatalog:
        data_path = Path(path)
        try:
            raw = json.loads(data_path.read_text(encoding="utf-8"))
        except OSError as error:
            raise EcopontoDataError(
                f"Nao foi possivel ler os dados dos Ecopontos: {data_path}"
            ) from error
        except json.JSONDecodeError as error:
            raise EcopontoDataError(
                f"JSON invalido nos dados dos Ecopontos: {data_path}"
            ) from error

        if not isinstance(raw, dict):
            raise EcopontoDataError("Os dados dos Ecopontos devem ser um objeto.")

        municipio = _text(raw.get("municipio"), "municipio")
        fonte = raw.get("fonte")
        if not isinstance(fonte, dict):
            raise EcopontoDataError("O campo 'fonte' deve ser um objeto.")
        observacoes = _text_list(raw.get("observacoes"), "observacoes")
        ecopontos_raw = raw.get("ecopontos")
        if not isinstance(ecopontos_raw, list) or not ecopontos_raw:
            raise EcopontoDataError("O campo 'ecopontos' deve ser uma lista.")

        ecopontos: list[Ecoponto] = []
        ids: set[str] = set()
        for item in ecopontos_raw:
            if not isinstance(item, dict):
                raise EcopontoDataError(
                    "Cada item de 'ecopontos' deve ser um objeto."
                )
            ecoponto_id = _text(item.get("id"), "ecoponto.id")
            if ecoponto_id in ids:
                raise EcopontoDataError(
                    f"ID de Ecoponto duplicado: {ecoponto_id}"
                )
            ids.add(ecoponto_id)
            ecopontos.append(
                Ecoponto(
                    id=ecoponto_id,
                    nome=_text(item.get("nome"), "ecoponto.nome"),
                    endereco=_text(
                        item.get("endereco"),
                        "ecoponto.endereco",
                    ),
                    horario=_text(item.get("horario"), "ecoponto.horario"),
                    materiais_aceitos=_text_list(
                        item.get("materiais_aceitos"),
                        "ecoponto.materiais_aceitos",
                    ),
                    materiais_nao_aceitos=_text_list(
                        item.get("materiais_nao_aceitos"),
                        "ecoponto.materiais_nao_aceitos",
                    ),
                    situacao=_text(
                        item.get("situacao"),
                        "ecoponto.situacao",
                    ),
                )
            )

        comunicados_raw = raw.get("comunicados", [])
        if not isinstance(comunicados_raw, list):
            raise EcopontoDataError(
                "O campo 'comunicados' deve ser uma lista."
            )

        comunicados: list[Comunicado] = []
        for item in comunicados_raw:
            if not isinstance(item, dict):
                raise EcopontoDataError(
                    "Cada item de 'comunicados' deve ser um objeto."
                )
            ecoponto_id = _text(
                item.get("ecoponto_id"),
                "comunicado.ecoponto_id",
            )
            if ecoponto_id not in ids:
                raise EcopontoDataError(
                    "Comunicado referencia Ecoponto inexistente: "
                    f"{ecoponto_id}"
                )
            alternativas_raw = item.get(
                "alternativas_durante_interdicao",
                {},
            )
            if not isinstance(alternativas_raw, dict):
                raise EcopontoDataError(
                    "O campo 'alternativas_durante_interdicao' deve ser "
                    "um objeto."
                )
            alternativas = tuple(
                f"{chave}: {valor}"
                for chave, valor in alternativas_raw.items()
            )
            comunicados.append(
                Comunicado(
                    id=_text(item.get("id"), "comunicado.id"),
                    ecoponto_id=ecoponto_id,
                    publicado_em=_date(
                        item.get("publicado_em"),
                        "comunicado.publicado_em",
                    ),
                    interdicao_inicio=_date(
                        item.get("interdicao_inicio"),
                        "comunicado.interdicao_inicio",
                    ),
                    interdicao_fim=_date(
                        item.get("interdicao_fim"),
                        "comunicado.interdicao_fim",
                    ),
                    reabertura_em=_date(
                        item.get("reabertura_em"),
                        "comunicado.reabertura_em",
                    ),
                    horario_apos_reabertura=_text(
                        item.get("horario_apos_reabertura"),
                        "comunicado.horario_apos_reabertura",
                    ),
                    materiais_aceitos_apos_reabertura=_text_list(
                        item.get("materiais_aceitos_apos_reabertura"),
                        "comunicado.materiais_aceitos_apos_reabertura",
                    ),
                    materiais_removidos_apos_reabertura=_text_list(
                        item.get("materiais_removidos_apos_reabertura"),
                        "comunicado.materiais_removidos_apos_reabertura",
                    ),
                    alternativas_durante_interdicao=alternativas,
                    observacao=_text(
                        item.get("observacao"),
                        "comunicado.observacao",
                    ),
                )
            )

        return cls(
            municipio=municipio,
            fonte=dict(fonte),
            observacoes=observacoes,
            ecopontos=tuple(ecopontos),
            comunicados=tuple(comunicados),
        )

    def query(
        self,
        nome: str | None = None,
        material: str | None = None,
        as_of: date | str | None = None,
    ) -> list[EcopontoStatus]:
        reference = _coerce_date(as_of)
        statuses = [
            self._status(ecoponto, reference, material)
            for ecoponto in self.ecopontos
        ]

        if material:
            accepted_names = [
                status.ecoponto.nome
                for status in statuses
                if status.aceita_material and status.situacao != "interditado"
            ]
            statuses = [
                replace(
                    status,
                    alternativas=(
                        status.alternativas
                        if status.alternativas
                        else tuple(
                            name
                            for name in accepted_names
                            if name != status.ecoponto.nome
                        )
                    ),
                )
                for status in statuses
            ]

        if nome:
            normalized_name = normalize_text(nome)
            statuses = [
                status
                for status in statuses
                if _name_matches(normalized_name, status.ecoponto.nome)
            ]

        return statuses

    def _status(
        self,
        ecoponto: Ecoponto,
        as_of: date,
        material: str | None,
    ) -> EcopontoStatus:
        comunicado = self._applicable_comunicado(ecoponto.id, as_of)
        situacao = ecoponto.situacao
        horario = ecoponto.horario
        aceitos = ecoponto.materiais_aceitos
        nao_aceitos = ecoponto.materiais_nao_aceitos
        aviso = ""
        alternativas: tuple[str, ...] = ()

        if comunicado is not None:
            if as_of < comunicado.interdicao_inicio:
                aviso = (
                    "Interdição programada a partir de "
                    f"{comunicado.interdicao_inicio.isoformat()}."
                )
            elif as_of <= comunicado.interdicao_fim:
                situacao = "interditado"
                horario = (
                    "fechado para obras de "
                    f"{comunicado.interdicao_inicio.isoformat()} a "
                    f"{comunicado.interdicao_fim.isoformat()}"
                )
                aceitos = ()
                alternativas = comunicado.alternativas_durante_interdicao
                aviso = comunicado.observacao
            else:
                situacao = "em funcionamento"
                horario = comunicado.horario_apos_reabertura
                aceitos = comunicado.materiais_aceitos_apos_reabertura
                nao_aceitos = _merge_terms(
                    nao_aceitos,
                    comunicado.materiais_removidos_apos_reabertura,
                )
                aviso = (
                    "Horário e materiais alterados pelo comunicado de "
                    f"{comunicado.publicado_em.isoformat()}; reaberto em "
                    f"{comunicado.reabertura_em.isoformat()}."
                )

        aceita_material: bool | None = None
        if material:
            aceita_material = (
                situacao != "interditado"
                and _accepts_material(aceitos, material)
            )

        return EcopontoStatus(
            ecoponto=ecoponto,
            as_of=as_of,
            situacao=situacao,
            horario=horario,
            materiais_aceitos=aceitos,
            materiais_nao_aceitos=nao_aceitos,
            material_consultado=material or "",
            aceita_material=aceita_material,
            aviso=aviso,
            alternativas=alternativas,
        )

    def _applicable_comunicado(
        self,
        ecoponto_id: str,
        as_of: date,
    ) -> Comunicado | None:
        applicable = [
            comunicado
            for comunicado in self.comunicados
            if comunicado.ecoponto_id == ecoponto_id
            and comunicado.publicado_em <= as_of
        ]
        if not applicable:
            return None
        return max(applicable, key=lambda item: item.publicado_em)


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EcopontoDataError(f"O campo '{field}' deve ser texto nao vazio.")
    return " ".join(value.split())


def _text_list(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise EcopontoDataError(f"O campo '{field}' deve ser uma lista.")
    result: list[str] = []
    for item in value:
        result.append(_text(item, field))
    return tuple(result)


def _date(value: object, field: str) -> date:
    if not isinstance(value, str):
        raise EcopontoDataError(f"O campo '{field}' deve ser uma data ISO.")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise EcopontoDataError(
            f"O campo '{field}' deve ser uma data ISO valida."
        ) from error


def _coerce_date(value: date | str | None) -> date:
    if value is None:
        return date.today()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(
            "A data de referencia deve estar no formato ISO AAAA-MM-DD."
        ) from error


def _name_matches(normalized_query: str, name: str) -> bool:
    normalized_name = normalize_text(name)
    if normalized_query in normalized_name:
        return True
    query_tokens = set(normalized_query.split())
    name_tokens = set(normalized_name.split())
    return bool(query_tokens) and query_tokens.issubset(name_tokens)


def _accepts_material(accepted: tuple[str, ...], material: str) -> bool:
    parts = [
        part.strip()
        for part in normalize_text(material).split(" e ")
        if part.strip()
    ]
    if not parts:
        return False
    return all(
        any(_term_matches(part, item) for item in accepted)
        for part in parts
    )


def _term_matches(term: str, item: str) -> bool:
    normalized_item = normalize_text(item)
    return (
        term == normalized_item
        or term in normalized_item
        or normalized_item in term
        or term.rstrip("s") == normalized_item.rstrip("s")
    )


def _merge_terms(
    current: tuple[str, ...],
    extra: tuple[str, ...],
) -> tuple[str, ...]:
    result: list[str] = []
    for term in current + extra:
        if term not in result:
            result.append(term)
    return tuple(result)


__all__ = [
    "Comunicado",
    "Ecoponto",
    "EcopontoCatalog",
    "EcopontoDataError",
    "EcopontoStatus",
]
