from __future__ import annotations

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.utils import embedding_functions

from vn_tax_rag.config import Settings


def get_client(settings: Settings) -> chromadb.PersistentClient:
    settings.chroma_path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(settings.chroma_path))


def get_embedding_function(settings: Settings):
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=settings.embedding_model
    )


def get_collection(settings: Settings, *, reset: bool = False) -> Collection:
    client = get_client(settings)
    if reset and settings.collection_name in [c.name for c in client.list_collections()]:
        client.delete_collection(settings.collection_name)
    return client.get_or_create_collection(
        name=settings.collection_name,
        embedding_function=get_embedding_function(settings),
        metadata={"hnsw:space": "cosine"},
    )


def collection_exists(settings: Settings) -> bool:
    client = get_client(settings)
    return settings.collection_name in [c.name for c in client.list_collections()]


def upsert_chunks(
    collection: Collection,
    ids: list[str],
    documents: list[str],
    metadatas: list[dict],
) -> None:
    batch_size = 64
    for start in range(0, len(ids), batch_size):
        end = start + batch_size
        collection.upsert(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
        )
