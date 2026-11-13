from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.errors import NotFoundError

from ..config import get_settings
from ..ingestion import Chunk
from .embeddings import EmbeddingModel, LocalEmbeddingModel

COLLECTION_FIXO = "ecocidadao_fixo"
COLLECTION_MARKDOWN = "ecocidadao_markdown"
COLLECTION_BY_STRATEGY = {
    "fixo": COLLECTION_FIXO,
    "markdown": COLLECTION_MARKDOWN,
}
COLLECTION_NAMES = (COLLECTION_FIXO, COLLECTION_MARKDOWN)

_METADATA_JSON_KEY = "_metadata_json"


class VectorStoreError(RuntimeError):
    pass


class CollectionNotFoundError(VectorStoreError):
    pass


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    text: str
    metadata: dict[str, Any]
    distance: float
    similarity: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "metadata": dict(self.metadata),
            "distance": self.distance,
            "similarity": self.similarity,
        }


@dataclass(frozen=True)
class IndexResult:
    collection_name: str
    indexed: int
    deleted: int
    total: int


def _serialize_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    serialized: dict[str, Any] = {}
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            serialized[key] = value
        else:
            serialized[key] = json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
            )

    serialized[_METADATA_JSON_KEY] = json.dumps(
        metadata,
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )
    return serialized


def _deserialize_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    if not metadata:
        return {}

    raw_metadata = metadata.get(_METADATA_JSON_KEY)
    if raw_metadata:
        parsed = json.loads(raw_metadata)
        if isinstance(parsed, dict):
            return parsed

    return {
        key: value
        for key, value in metadata.items()
        if key != _METADATA_JSON_KEY
    }


class ChromaVectorStore:
    def __init__(
        self,
        collection_name: str,
        chroma_dir: Path | str | None = None,
        embedding_model: EmbeddingModel | None = None,
        batch_size: int = 32,
        client: Any | None = None,
    ) -> None:
        if not collection_name.strip():
            raise ValueError("O nome da colecao nao pode ser vazio.")

        settings = get_settings()
        self.collection_name = collection_name
        self.chroma_dir = Path(chroma_dir or settings.chroma_dir)
        self.embedding_model = embedding_model or LocalEmbeddingModel()
        self.batch_size = batch_size
        self._client = client
        self._collection: Any | None = None

    @property
    def client(self) -> Any:
        if self._client is None:
            self.chroma_dir.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=str(self.chroma_dir),
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self._client

    def get_collection(self, create: bool = True) -> Any:
        if self._collection is not None:
            return self._collection

        if create:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        else:
            try:
                self._collection = self.client.get_collection(
                    name=self.collection_name,
                )
            except NotFoundError as error:
                raise CollectionNotFoundError(
                    f"Colecao nao encontrada: {self.collection_name}"
                ) from error

        return self._collection

    @classmethod
    def load(
        cls,
        collection_name: str,
        chroma_dir: Path | str | None = None,
        embedding_model: EmbeddingModel | None = None,
        batch_size: int = 32,
    ) -> ChromaVectorStore:
        store = cls(
            collection_name=collection_name,
            chroma_dir=chroma_dir,
            embedding_model=embedding_model,
            batch_size=batch_size,
        )
        store.get_collection(create=False)
        return store

    def create_or_update(
        self,
        chunks: Iterable[Chunk],
        replace_existing: bool = False,
    ) -> IndexResult:
        unique_chunks = {
            chunk.chunk_id: chunk
            for chunk in chunks
            if chunk.chunk_id and chunk.text.strip()
        }
        if not unique_chunks:
            raise ValueError("Nenhum chunk valido foi informado.")

        if replace_existing:
            self.delete_collection()
            self._collection = None

        collection = self.get_collection(create=True)

        if not replace_existing:
            existing_ids = set(collection.get().get("ids", []))
        else:
            existing_ids = set()

        ordered_ids = sorted(unique_chunks)
        deleted = 0

        for start in range(0, len(ordered_ids), self.batch_size):
            batch_ids = ordered_ids[start : start + self.batch_size]
            batch_chunks = [unique_chunks[chunk_id] for chunk_id in batch_ids]
            embeddings = self.embedding_model.embed_documents(
                [chunk.text for chunk in batch_chunks]
            )
            collection.upsert(
                ids=batch_ids,
                embeddings=embeddings,
                documents=[chunk.text for chunk in batch_chunks],
                metadatas=[
                    _serialize_metadata(chunk.metadata)
                    for chunk in batch_chunks
                ],
            )

        stale_ids = sorted(existing_ids - set(ordered_ids))
        if stale_ids:
            collection.delete(ids=stale_ids)
            deleted = len(stale_ids)

        return IndexResult(
            collection_name=self.collection_name,
            indexed=len(ordered_ids),
            deleted=deleted,
            total=collection.count(),
        )

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[RetrievedChunk]:
        if not query_text.strip():
            raise ValueError("A consulta nao pode ser vazia.")
        if top_k < 1:
            raise ValueError("top_k deve ser maior ou igual a 1.")

        collection = self.get_collection(create=False)
        query_embedding = self.embedding_model.embed_query(query_text)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        retrieved: list[RetrievedChunk] = []
        for chunk_id, text, metadata, distance in zip(
            ids,
            documents,
            metadatas,
            distances,
        ):
            distance_value = float(distance)
            retrieved.append(
                RetrievedChunk(
                    chunk_id=str(chunk_id),
                    text=str(text or ""),
                    metadata=_deserialize_metadata(metadata),
                    distance=distance_value,
                    similarity=1.0 - distance_value,
                )
            )

        return retrieved

    def count(self) -> int:
        return int(self.get_collection(create=False).count())

    def list_collections(self) -> list[str]:
        return [collection.name for collection in self.client.list_collections()]

    def delete_collection(self) -> None:
        try:
            self.client.delete_collection(name=self.collection_name)
        except NotFoundError:
            pass
        finally:
            self._collection = None

    def get_by_ids(self, chunk_ids: Iterable[str]) -> list[RetrievedChunk]:
        ids = sorted(set(chunk_ids))
        if not ids:
            return []

        collection = self.get_collection(create=False)
        results = collection.get(
            ids=ids,
            include=["documents", "metadatas"],
        )
        metadatas = results.get("metadatas") or []
        documents = results.get("documents") or []

        return [
            RetrievedChunk(
                chunk_id=str(chunk_id),
                text=str(document or ""),
                metadata=_deserialize_metadata(metadata),
                distance=0.0,
                similarity=1.0,
            )
            for chunk_id, document, metadata in zip(
                results.get("ids", []),
                documents,
                metadatas,
            )
        ]


def create_index(
    strategy: str,
    chunks: Iterable[Chunk],
    chroma_dir: Path | str | None = None,
    embedding_model: EmbeddingModel | None = None,
    replace_existing: bool = False,
) -> IndexResult:
    collection_name = COLLECTION_BY_STRATEGY.get(strategy)
    if collection_name is None:
        raise ValueError(
            f"Estrategia invalida: {strategy!r}. Use 'fixo' ou 'markdown'."
        )

    store = ChromaVectorStore(
        collection_name=collection_name,
        chroma_dir=chroma_dir,
        embedding_model=embedding_model,
    )
    return store.create_or_update(
        chunks,
        replace_existing=replace_existing,
    )


def load_collection(
    collection_name: str,
    chroma_dir: Path | str | None = None,
    embedding_model: EmbeddingModel | None = None,
) -> ChromaVectorStore:
    return ChromaVectorStore.load(
        collection_name=collection_name,
        chroma_dir=chroma_dir,
        embedding_model=embedding_model,
    )
