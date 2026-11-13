from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Literal

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from .loader import Document, count_words

FIXED_CHUNK_SIZE = 800
FIXED_CHUNK_OVERLAP = 150
MARKDOWN_CHUNK_SIZE = 800
MARKDOWN_CHUNK_OVERLAP = 100
Strategy = Literal["fixo", "markdown"]

_SEPARATORS = ["\n\n", "\n", ". ", "; ", ", ", " ", ""]
_HEADER_KEYS = ("h1", "h2", "h3")
_HEADERS_TO_SPLIT_ON = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
]


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    text: str
    metadata: dict[str, Any]
    chunk_index: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "text": self.text,
            "metadata": dict(self.metadata),
        }


def _base_metadata(document: Document) -> dict[str, Any]:
    metadata = dict(document.metadata)
    metadata.update(
        {
            "doc_id": document.doc_id,
            "source_file": document.path.name,
            "document_content_hash": document.content_hash,
        }
    )
    return metadata


def _section_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    section_values = [
        str(metadata[key]).strip()
        for key in _HEADER_KEYS
        if metadata.get(key)
    ]
    section_metadata = {
        f"section_{key}": metadata.get(key)
        for key in _HEADER_KEYS
    }
    section_metadata.update(
        {
            "section_path": section_values,
            "section_path_text": " > ".join(section_values),
            "section_level": len(section_values),
        }
    )
    return section_metadata


def _make_chunk(
    document: Document,
    text: str,
    index: int,
    strategy: Strategy,
    metadata: dict[str, Any],
    chunk_size: int,
    chunk_overlap: int,
) -> Chunk:
    chunk_id = f"{document.doc_id}::{strategy}::{index:04d}"
    chunk_metadata = dict(metadata)
    chunk_metadata.update(
        {
            "chunk_id": chunk_id,
            "chunk_index": index,
            "chunk_strategy": strategy,
            "chunk_size_limit": chunk_size,
            "chunk_overlap": chunk_overlap,
            "char_count": len(text),
            "word_count": count_words(text),
            "chunk_content_hash": hashlib.sha256(
                text.encode("utf-8")
            ).hexdigest(),
        }
    )
    return Chunk(
        chunk_id=chunk_id,
        doc_id=document.doc_id,
        text=text,
        metadata=chunk_metadata,
        chunk_index=index,
    )


def _chunk_fixed(document: Document) -> list[Chunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=FIXED_CHUNK_SIZE,
        chunk_overlap=FIXED_CHUNK_OVERLAP,
        separators=_SEPARATORS,
        length_function=len,
    )
    texts = [
        text
        for text in splitter.split_text(document.content)
        if text.strip()
    ]
    base_metadata = _base_metadata(document)

    return [
        _make_chunk(
            document=document,
            text=text,
            index=index,
            strategy="fixo",
            metadata=base_metadata,
            chunk_size=FIXED_CHUNK_SIZE,
            chunk_overlap=FIXED_CHUNK_OVERLAP,
        )
        for index, text in enumerate(texts)
    ]


def _chunk_markdown(document: Document) -> list[Chunk]:
    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=_HEADERS_TO_SPLIT_ON,
        strip_headers=False,
    )
    recursive_splitter = RecursiveCharacterTextSplitter(
        chunk_size=MARKDOWN_CHUNK_SIZE,
        chunk_overlap=MARKDOWN_CHUNK_OVERLAP,
        separators=_SEPARATORS,
        length_function=len,
    )

    sections = header_splitter.split_text(document.content)
    base_metadata = _base_metadata(document)
    chunks: list[Chunk] = []
    index = 0

    for section in sections:
        if not section.page_content.strip():
            continue

        section_metadata = _section_metadata(section.metadata)
        section_metadata = {**base_metadata, **section_metadata}
        section_texts = recursive_splitter.split_text(section.page_content)

        for text in section_texts:
            if not text.strip():
                continue

            chunks.append(
                _make_chunk(
                    document=document,
                    text=text,
                    index=index,
                    strategy="markdown",
                    metadata=section_metadata,
                    chunk_size=MARKDOWN_CHUNK_SIZE,
                    chunk_overlap=MARKDOWN_CHUNK_OVERLAP,
                )
            )
            index += 1

    return chunks


def chunk_documents(
    documents: list[Document],
    strategy: Strategy,
) -> list[Chunk]:
    if strategy == "fixo":
        chunker = _chunk_fixed
    elif strategy == "markdown":
        chunker = _chunk_markdown
    else:
        raise ValueError(
            f"Estrategia de chunking invalida: {strategy!r}. "
            "Use 'fixo' ou 'markdown'."
        )

    chunks: list[Chunk] = []
    for document in sorted(documents, key=lambda item: item.doc_id):
        chunks.extend(chunker(document))

    return chunks
