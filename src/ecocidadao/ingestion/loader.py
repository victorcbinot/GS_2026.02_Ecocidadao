from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

REQUIRED_METADATA = ("titulo", "data_publicacao", "tema")
EXPECTED_DOCUMENT_IDS = (
    "regulamento_descarte",
    "lista_ecopontos",
    "comunicado_interdicao",
)
MIN_DOCUMENT_WORDS = 100
_WORD_PATTERN = re.compile(r"\b[\wÀ-ÿ]+\b", re.UNICODE)


class DocumentValidationError(ValueError):
    pass


@dataclass(frozen=True)
class Document:
    doc_id: str
    path: Path
    titulo: str
    data_publicacao: str
    tema: str
    metadata: dict[str, Any]
    content: str
    raw_content: str
    word_count: int
    content_hash: str

    def summary(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "source_file": self.path.name,
            "titulo": self.titulo,
            "data_publicacao": self.data_publicacao,
            "tema": self.tema,
            "word_count": self.word_count,
            "content_hash": self.content_hash,
            "metadata": dict(self.metadata),
        }


def count_words(text: str) -> int:
    return len(_WORD_PATTERN.findall(text))


def _split_front_matter(
    raw_content: str,
    path: Path,
) -> tuple[dict[str, Any], str]:
    lines = raw_content.splitlines(keepends=True)

    if not lines or lines[0].strip() != "---":
        raise DocumentValidationError(
            f"{path.name}: front matter ausente ou delimitador inicial invalido."
        )

    closing_index: int | None = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing_index = index
            break

    if closing_index is None:
        raise DocumentValidationError(
            f"{path.name}: delimitador final do front matter nao encontrado."
        )

    front_matter_text = "".join(lines[1:closing_index])
    try:
        front_matter = yaml.safe_load(front_matter_text)
    except yaml.YAMLError as error:
        raise DocumentValidationError(
            f"{path.name}: front matter YAML invalido: {error}"
        ) from error

    if not isinstance(front_matter, dict):
        raise DocumentValidationError(
            f"{path.name}: front matter deve ser um mapa de metadados."
        )

    body = "".join(lines[closing_index + 1 :])
    return front_matter, body


def _to_iso_date(value: Any, path: Path) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if not isinstance(value, str) or not value.strip():
        raise DocumentValidationError(
            f"{path.name}: data_publicacao deve ser uma data ISO valida."
        )

    normalized = value.strip()
    try:
        return date.fromisoformat(normalized).isoformat()
    except ValueError as error:
        raise DocumentValidationError(
            f"{path.name}: data_publicacao invalida: {normalized!r}."
        ) from error


def _normalize_metadata(
    front_matter: dict[str, Any],
    path: Path,
) -> dict[str, Any]:
    metadata = dict(front_matter)

    for key, value in list(metadata.items()):
        if isinstance(value, datetime):
            metadata[key] = value.date().isoformat()
        elif isinstance(value, date):
            metadata[key] = value.isoformat()
        elif isinstance(value, Path):
            metadata[key] = str(value)

    for key in REQUIRED_METADATA:
        value = metadata.get(key)
        if not isinstance(value, str) or not value.strip():
            raise DocumentValidationError(
                f"{path.name}: metadado obrigatorio ausente ou vazio: {key}."
            )

    metadata["titulo"] = metadata["titulo"].strip()
    metadata["tema"] = metadata["tema"].strip()
    metadata["data_publicacao"] = _to_iso_date(
        metadata["data_publicacao"],
        path,
    )

    for key, value in metadata.items():
        if value is None:
            raise DocumentValidationError(
                f"{path.name}: metadado adicional vazio: {key}."
            )
        if isinstance(value, str) and not value.strip():
            raise DocumentValidationError(
                f"{path.name}: metadado adicional vazio: {key}."
            )
        if isinstance(value, (list, dict)) and not value:
            raise DocumentValidationError(
                f"{path.name}: metadado adicional vazio: {key}."
            )

    return metadata


def load_document(path: Path) -> Document:
    resolved_path = Path(path).resolve()
    if not resolved_path.is_file():
        raise FileNotFoundError(f"Documento nao encontrado: {resolved_path}")

    raw_content = resolved_path.read_text(encoding="utf-8")
    front_matter, content = _split_front_matter(raw_content, resolved_path)
    metadata = _normalize_metadata(front_matter, resolved_path)

    word_count = count_words(content)
    if word_count < MIN_DOCUMENT_WORDS:
        raise DocumentValidationError(
            f"{resolved_path.name}: documento tem {word_count} palavras; "
            f"o minimo e {MIN_DOCUMENT_WORDS}."
        )

    doc_id = resolved_path.stem.strip()
    if not doc_id:
        raise DocumentValidationError(
            f"{resolved_path.name}: nao foi possivel derivar o doc_id."
        )

    return Document(
        doc_id=doc_id,
        path=resolved_path,
        titulo=metadata["titulo"],
        data_publicacao=metadata["data_publicacao"],
        tema=metadata["tema"],
        metadata=metadata,
        content=content,
        raw_content=raw_content,
        word_count=word_count,
        content_hash=hashlib.sha256(raw_content.encode("utf-8")).hexdigest(),
    )


def load_documents(directory: Path) -> list[Document]:
    resolved_directory = Path(directory).resolve()
    if not resolved_directory.is_dir():
        raise FileNotFoundError(
            f"Diretorio da base documental nao encontrado: {resolved_directory}"
        )

    paths = sorted(resolved_directory.glob("*.md"))
    if not paths:
        raise DocumentValidationError(
            f"Nenhum documento Markdown encontrado em {resolved_directory}."
        )

    documents = [load_document(path) for path in paths]
    document_ids = [document.doc_id for document in documents]
    if len(document_ids) != len(set(document_ids)):
        raise DocumentValidationError(
            "Ha documentos com doc_id duplicado na base documental."
        )

    return documents


def validate_expected_documents(
    documents: list[Document],
    expected: tuple[str, ...] = EXPECTED_DOCUMENT_IDS,
) -> None:
    found = {document.doc_id for document in documents}
    missing = [doc_id for doc_id in expected if doc_id not in found]
    if missing:
        raise DocumentValidationError(
            "Documentos obrigatorios ausentes: " + ", ".join(missing) + "."
        )
