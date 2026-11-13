from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any

from .vector_store import RetrievedChunk

_MONTHS = (
    "janeiro",
    "fevereiro",
    "marco",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
)
_MONTH_PATTERN = "|".join(_MONTHS)
_DATE_PATTERNS = (
    re.compile(
        rf"\b\d{{1,2}}(?:º|o)?\s+de\s+(?:{_MONTH_PATTERN})"
        rf"\s+de\s+\d{{4}}\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b\d{1,2}/\d{1,2}/\d{4}\b"),
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
)


def extract_date_mentions(text: str) -> tuple[str, ...]:
    mentions: list[str] = []
    seen: set[str] = set()

    for pattern in _DATE_PATTERNS:
        for match in pattern.finditer(text):
            value = " ".join(match.group(0).split())
            normalized = value.casefold()
            if normalized not in seen:
                seen.add(normalized)
                mentions.append(value)

    return tuple(mentions)


def _as_iso_date(value: date | str | None) -> str:
    if value is None:
        return date.today().isoformat()
    if isinstance(value, date):
        return value.isoformat()

    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as error:
        raise ValueError(
            "A data de referência deve estar no formato ISO AAAA-MM-DD."
        ) from error


@dataclass(frozen=True)
class Source:
    label: str
    chunk_id: str
    doc_id: str
    title: str
    publication_date: str
    topic: str
    source_file: str
    section: str
    text: str
    similarity: float
    metadata: dict[str, Any]
    dates_mentioned: tuple[str, ...]

    @classmethod
    def from_retrieved(
        cls,
        label: str,
        retrieved: RetrievedChunk,
    ) -> Source:
        metadata = dict(retrieved.metadata)
        section = (
            metadata.get("section_path_text")
            or " > ".join(metadata.get("section_path") or [])
            or "Não informada"
        )
        return cls(
            label=label,
            chunk_id=retrieved.chunk_id,
            doc_id=str(metadata.get("doc_id") or "documento"),
            title=str(
                metadata.get("titulo")
                or metadata.get("doc_id")
                or "Documento"
            ),
            publication_date=str(
                metadata.get("data_publicacao") or "Não informada"
            ),
            topic=str(metadata.get("tema") or "Não informado"),
            source_file=str(
                metadata.get("source_file")
                or metadata.get("doc_id")
                or "Não informado"
            ),
            section=str(section),
            text=retrieved.text,
            similarity=retrieved.similarity,
            metadata=metadata,
            dates_mentioned=extract_date_mentions(retrieved.text),
        )

    def citation(self) -> str:
        return (
            f"[{self.label}] {self.title} "
            f"(documento: {self.doc_id}; publicado em: "
            f"{self.publication_date}; seção: {self.section}; "
            f"arquivo: {self.source_file})"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "title": self.title,
            "publication_date": self.publication_date,
            "topic": self.topic,
            "source_file": self.source_file,
            "section": self.section,
            "text": self.text,
            "similarity": self.similarity,
            "dates_mentioned": list(self.dates_mentioned),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ContextBundle:
    text: str
    sources: list[Source]
    temporal_notes: str
    as_of: str
    question_dates: tuple[str, ...]

    def source_by_label(self, label: str) -> Source | None:
        normalized = label.upper()
        for source in self.sources:
            if source.label.upper() == normalized:
                return source
        return None


def _extra_metadata_lines(source: Source) -> list[str]:
    lines: list[str] = []
    for key, label in (
        ("municipio", "Município"),
        ("orgao", "Órgão"),
        ("versao", "Versão"),
    ):
        value = source.metadata.get(key)
        if value:
            lines.append(f"{label}: {value}")
    return lines


def _format_source_block(source: Source) -> str:
    lines = [
        f"[{source.label}]",
        f"Documento: {source.doc_id}",
        f"Título: {source.title}",
        f"Publicado em: {source.publication_date}",
        f"Tema: {source.topic}",
        f"Seção: {source.section}",
        f"Arquivo: {source.source_file}",
        f"Similaridade: {source.similarity:.4f}",
    ]
    lines.extend(_extra_metadata_lines(source))

    if source.dates_mentioned:
        lines.append(
            "Datas mencionadas no trecho: "
            + "; ".join(source.dates_mentioned)
        )

    lines.extend(["Trecho:", source.text.strip()])
    return "\n".join(lines)


def _temporal_notes(
    sources: list[Source],
    as_of: str,
    question_dates: tuple[str, ...],
) -> str:
    lines = [
        f"Data de referência: {as_of}",
        "Datas mencionadas na pergunta: "
        + (", ".join(question_dates) if question_dates else "nenhuma"),
        "Orientação de vigência:",
        (
            "- A data de publicação do documento é um indício, não a data "
            "de vigência da regra."
        ),
        (
            "- Aplique expressões como 'a partir de', 'até', 'durante' e "
            "'após' conforme o texto do documento."
        ),
        (
            "- Se a pergunta indicar uma data, responda para essa data. "
            "Se não indicar, responda para a data de referência e informe "
            "isso."
        ),
        (
            "- Não aplique regras de reabertura ou mudança a períodos "
            "anteriores ao início expresso."
        ),
        (
            "- Não use documento publicado depois da data da pergunta para "
            "descrever regras vigentes nessa data, salvo vigência retroativa "
            "expressa."
        ),
        "- Não misture regras antigas e novas.",
        "Documentos recuperados:",
    ]

    for source in sources:
        dates = (
            "; ".join(source.dates_mentioned)
            if source.dates_mentioned
            else "nenhuma data explícita no trecho"
        )
        lines.append(
            f"- {source.label}: publicado em {source.publication_date}; "
            f"título: {source.title}; datas no trecho: {dates}"
        )

    return "\n".join(lines)


def build_context(
    question: str,
    retrieved: list[RetrievedChunk],
    as_of: date | str | None = None,
    max_chars: int | None = None,
) -> ContextBundle:
    as_of_iso = _as_iso_date(as_of)
    question_dates = extract_date_mentions(question)
    sources = [
        Source.from_retrieved(f"F{index}", chunk)
        for index, chunk in enumerate(retrieved, start=1)
    ]
    notes = _temporal_notes(sources, as_of_iso, question_dates)

    blocks: list[str] = []
    used_sources: list[Source] = []
    current_length = 0

    for source in sources:
        block = _format_source_block(source)
        separator = "\n\n" if blocks else ""
        required = len(separator) + len(block)

        if max_chars is not None and current_length + required > max_chars:
            remaining = max_chars - current_length - len(separator)
            if remaining > 200:
                blocks.append(separator + block[:remaining].rstrip())
                used_sources.append(source)
            break

        blocks.append(separator + block)
        used_sources.append(source)
        current_length += required

    return ContextBundle(
        text="\n".join(blocks),
        sources=used_sources,
        temporal_notes=notes,
        as_of=as_of_iso,
        question_dates=question_dates,
    )
