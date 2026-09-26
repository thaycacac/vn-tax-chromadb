from __future__ import annotations

from typing import Any

from chromadb.api.models.Collection import Collection


def retrieve(
    collection: Collection,
    question: str,
    n_results: int = 4,
    tax_type: str | None = None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "query_texts": [question],
        "n_results": n_results,
        "include": ["documents", "metadatas", "distances"],
    }
    if tax_type:
        kwargs["where"] = {"tax_type": tax_type.upper()}
    return collection.query(**kwargs)
